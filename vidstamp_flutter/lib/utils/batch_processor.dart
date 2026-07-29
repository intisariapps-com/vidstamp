import 'dart:io';
import 'dart:convert';
import '../utils/subtitle_processor.dart';
import '../utils/video_processor.dart';

/// Mewakili status satu episode dalam antrean batch
class EpisodeTask {
  final String videoPath;
  String status; // 'pending', 'processing', 'done', 'error'
  String? errorMessage;

  EpisodeTask({
    required this.videoPath,
    this.status = 'pending',
    this.errorMessage,
  });

  String get filename => videoPath.split(Platform.pathSeparator).last;
}

/// Hasil proses satu episode
class EpisodeResult {
  final String tempCleanVideoPath;
  final List<Map<String, dynamic>> shiftedSubtitles;
  final double episodeDuration;

  EpisodeResult({
    required this.tempCleanVideoPath,
    required this.shiftedSubtitles,
    required this.episodeDuration,
  });
}

class BatchProcessor {
  // Deteksi Opening & Ending menggunakan ffprobe untuk satu file video
  static Future<Map<String, double?>> detectOpeningEnding(
    String videoPath,
    String ffprobePath,
  ) async {
    Map<String, double?> result = {
      'opStart': null,
      'opEnd': null,
      'edStart': null,
      'edEnd': null,
    };

    if (!videoPath.toLowerCase().endsWith('.mkv')) return result;

    try {
      final res = await Process.run(ffprobePath, [
        '-v', 'error',
        '-show_chapters',
        '-print_format', 'json',
        videoPath,
      ]);

      if (res.exitCode == 0) {
        final jsonMap = json.decode(res.stdout as String);
        final chapters = jsonMap['chapters'] as List?;
        if (chapters != null) {
          for (var chapter in chapters) {
            final start = double.parse(chapter['start_time'].toString());
            final end = double.parse(chapter['end_time'].toString());
            final tags = chapter['tags'] as Map?;
            if (tags != null) {
              final title = tags['title'].toString().toLowerCase();
              if (title.contains('op') ||
                  title.contains('opening') ||
                  title.contains('intro')) {
                result['opStart'] = start;
                result['opEnd'] = end;
              } else if (title.contains('ed') ||
                  title.contains('ending') ||
                  title.contains('outro')) {
                result['edStart'] = start;
                result['edEnd'] = end;
              }
            }
          }
        }
      }
    } catch (e) {
      print('Gagal deteksi bab $videoPath: $e');
    }

    return result;
  }

  // Hitung keep ranges dari skip ranges
  static List<Map<String, double>> calcKeepRanges(
    List<Map<String, double>> skipRanges,
    double totalDuration,
  ) {
    final sortedSkips = List<Map<String, double>>.from(skipRanges)
      ..sort((a, b) => a['start']!.compareTo(b['start']!));

    final List<Map<String, double>> keepRanges = [];
    double cursor = 0.0;
    for (var skip in sortedSkips) {
      final sStart = skip['start']!;
      final sEnd = skip['end']!;
      if (sStart > cursor) {
        keepRanges.add({'start': cursor, 'end': sStart});
      }
      if (sEnd > cursor) cursor = sEnd;
    }
    if (cursor < totalDuration) {
      keepRanges.add({'start': cursor, 'end': totalDuration});
    }
    return keepRanges;
  }

  // Dapatkan durasi video menggunakan ffprobe
  static Future<double> getVideoDuration(
    String videoPath,
    String ffprobePath,
  ) async {
    try {
      final res = await Process.run(ffprobePath, [
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        videoPath,
      ]);
      if (res.exitCode == 0) {
        final jsonMap = json.decode(res.stdout as String);
        final dur = jsonMap['format']?['duration'];
        if (dur != null) {
          return double.parse(dur.toString());
        }
      }
    } catch (e) {
      print('Gagal mendapatkan durasi $videoPath: $e');
    }
    return 0.0;
  }

  // Proses satu episode: potong video & selaraskan subtitle
  static Future<EpisodeResult?> processEpisode({
    required String videoPath,
    required String ffmpegPath,
    required String ffprobePath,
    required String tempOutputVideoPath,
    required int lineLimit,
    required Function(String) onStatus,
  }) async {
    onStatus('Mendeteksi bab (OP/ED)...');

    // Deteksi Opening/Ending
    final opEd = await detectOpeningEnding(videoPath, ffprobePath);
    final opStart = opEd['opStart'];
    final opEnd = opEd['opEnd'];
    final edStart = opEd['edStart'];
    final edEnd = opEd['edEnd'];

    // Dapatkan durasi total
    final totalDuration = await getVideoDuration(videoPath, ffprobePath);
    if (totalDuration <= 0.0) {
      print('Durasi video tidak terdeteksi: $videoPath');
      return null;
    }

    // Bangun skip ranges
    final List<Map<String, double>> skipRanges = [];
    if (opStart != null && opEnd != null) {
      skipRanges.add({'start': opStart, 'end': opEnd});
    }
    if (edStart != null && edEnd != null) {
      skipRanges.add({'start': edStart, 'end': edEnd});
    }

    // Hitung keep ranges
    final keepRanges = skipRanges.isEmpty
        ? [{'start': 0.0, 'end': totalDuration}]
        : calcKeepRanges(skipRanges, totalDuration);

    // Hitung total durasi keep
    final keepDuration = keepRanges.fold<double>(
        0.0, (prev, r) => prev + (r['end']! - r['start']!));

    // Ekstrak subtitle
    onStatus('Mengekstrak subtitle...');
    final baseName = videoPath.substring(0, videoPath.lastIndexOf('.'));
    final uuidSuffix = DateTime.now().millisecondsSinceEpoch.toString();
    final tempExtractSrt = '${baseName}_temp_ep_$uuidSuffix.srt';
    final tempExtractAss = '${baseName}_temp_ep_$uuidSuffix.ass';
    final tempShiftedAss = '${baseName}_temp_shifted_$uuidSuffix.ass';
    final tempShiftedSrt = '${baseName}_temp_shifted_$uuidSuffix.srt';

    String? assPath;
    String? srtPath;

    if (videoPath.toLowerCase().endsWith('.mkv')) {
      await Process.run(ffmpegPath,
          ['-y', '-i', videoPath, '-map', '0:s:0', tempExtractSrt]);
      if (File(tempExtractSrt).existsSync()) srtPath = tempExtractSrt;

      await Process.run(ffmpegPath,
          ['-y', '-i', videoPath, '-map', '0:s:0', tempExtractAss]);
      if (File(tempExtractAss).existsSync()) assPath = tempExtractAss;
    }

    // Selaraskan subtitle
    onStatus('Menyelaraskan subtitle...');
    List<Map<String, dynamic>> shiftedSubs = [];

    if (srtPath != null) {
      SubtitleProcessor.cutAndShiftSrt(
        srtPath,
        keepRanges,
        tempShiftedSrt,
        lineLimit: lineLimit,
        inputAssPath: assPath,
      );
      // Parsing subtitle hasil shift
      if (File(tempShiftedSrt).existsSync()) {
        final content = File(tempShiftedSrt).readAsStringSync();
        final blocks = content.trim().split(RegExp(r'\n\s*\n'));
        for (var block in blocks) {
          final lines = block.trim().split('\n');
          int tsIdx = -1;
          for (var i = 0; i < lines.length; i++) {
            if (lines[i].contains('-->')) {
              tsIdx = i;
              break;
            }
          }
          if (tsIdx != -1) {
            final tsParts = lines[tsIdx].split('-->');
            if (tsParts.length == 2) {
              shiftedSubs.add({
                'start': SubtitleProcessor.srtTimeToSeconds(tsParts[0]),
                'end': SubtitleProcessor.srtTimeToSeconds(tsParts[1]),
                'text': lines.sublist(tsIdx + 1).join('\n'),
              });
            }
          }
        }
      }
    }

    // Potong video menggunakan FFmpeg concat filter
    onStatus('Merender potongan video...');
    final args = VideoProcessor.buildFfmpegArgs(
      videoPath: videoPath,
      keepRanges: keepRanges,
      outputPath: tempOutputVideoPath,
      mode: 'softsub', // Potong dulu tanpa hardsub
    );
    final renderResult = await Process.run(ffmpegPath, args);

    // Bersihkan berkas temp subtitle sementara
    for (var p in [tempExtractSrt, tempExtractAss, tempShiftedAss, tempShiftedSrt]) {
      try {
        File(p).deleteSync();
      } catch (_) {}
    }

    if (renderResult.exitCode != 0) {
      print('FFmpeg gagal pada episode: $videoPath\n${renderResult.stderr}');
      return null;
    }

    return EpisodeResult(
      tempCleanVideoPath: tempOutputVideoPath,
      shiftedSubtitles: shiftedSubs,
      episodeDuration: keepDuration,
    );
  }

  // Gabungkan semua potongan episode secara lossless menggunakan concat demuxer
  static Future<bool> concatEpisodesLossless({
    required List<String> tempVideoPaths,
    required String outputVideoPath,
    required String ffmpegPath,
  }) async {
    if (tempVideoPaths.isEmpty) return false;

    // Buat file daftar concat sementara di folder output
    final outputDir = File(outputVideoPath).parent.path;
    final listFile = File(
        '$outputDir${Platform.pathSeparator}mylist_temp_${DateTime.now().millisecondsSinceEpoch}.txt');

    try {
      final lines = tempVideoPaths.map((p) {
        // Gunakan path relatif untuk keamanan di Windows
        final relPath = p.replaceAll('\\', '/');
        return "file '$relPath'";
      }).join('\n');
      listFile.writeAsStringSync(lines);

      final res = await Process.run(ffmpegPath, [
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', listFile.path,
        '-c', 'copy',
        outputVideoPath,
      ]);

      return res.exitCode == 0;
    } catch (e) {
      print('Gagal concat lossless: $e');
      return false;
    } finally {
      try { listFile.deleteSync(); } catch (_) {}
    }
  }

  // Gabungkan semua subtitle global menjadi satu .srt
  static bool buildGlobalSubtitleSrt({
    required List<Map<String, dynamic>> globalSubs,
    required String outputSrtPath,
  }) {
    try {
      final deduped = SubtitleProcessor.mergeDuplicateOcrSubtitles(
        List<Map<String, dynamic>>.from(globalSubs),
      );

      final buffer = StringBuffer();
      for (var i = 0; i < deduped.length; i++) {
        final sub = deduped[i];
        final startStr = SubtitleProcessor.secondsToSrtTime(sub['start'] as double);
        final endStr = SubtitleProcessor.secondsToSrtTime(sub['end'] as double);
        buffer.writeln('${i + 1}');
        buffer.writeln('$startStr --> $endStr');
        buffer.writeln('${sub['text']}\n');
      }
      File(outputSrtPath).writeAsStringSync(buffer.toString().trim());
      return true;
    } catch (e) {
      print('Gagal menulis subtitle global: $e');
      return false;
    }
  }
}
