import 'dart:io';

class VideoProcessor {
  // 1. Resolusi Path FFmpeg
  static String? getFfmpegPath() {
    final envPath = Platform.environment['PATH'] ?? '';
    final separator = Platform.isWindows ? ';' : ':';
    final paths = envPath.split(separator);
    final ffmpegName = Platform.isWindows ? 'ffmpeg.exe' : 'ffmpeg';

    for (var path in paths) {
      final file = File('$path${Platform.pathSeparator}$ffmpegName');
      if (file.existsSync()) {
        return file.path;
      }
    }

    final localBin = Directory(Directory.current.path).parent.path;
    final fallbackFile = File(
      Platform.isWindows
          ? '$localBin${Platform.pathSeparator}bin${Platform.pathSeparator}win${Platform.pathSeparator}ffmpeg.exe'
          : '$localBin${Platform.pathSeparator}bin${Platform.pathSeparator}mac${Platform.pathSeparator}ffmpeg',
    );

    if (fallbackFile.existsSync()) {
      return fallbackFile.path;
    }

    return null;
  }

  // 2. Escape Path untuk Filter Complex FFmpeg
  static String escapePathForFfmpegFilter(String path) {
    var safe = path.replaceAll('\\', '/');
    safe = safe.replaceAll(':', '\\:');
    safe = safe.replaceAll("'", "'\\\\''");
    safe = safe.replaceAll(',', '\\,');
    return safe;
  }

  // 3. Bangun Argumen Command Concat & Hardsub
  static List<String> buildFfmpegArgs({
    required String videoPath,
    required List<Map<String, double>> keepRanges,
    required String outputPath,
    required String mode, // 'softsub' atau 'hardsub'
    String? shiftedAssPath,
    String? shiftedSrtPath,
    int? fontSize,
  }) {
    final List<String> args = ['-y', '-i', videoPath];

    // Bangun filter complex concat
    final List<String> filterVNodes = [];
    final List<String> filterANodes = [];

    for (var i = 0; i < keepRanges.length; i++) {
      final start = keepRanges[i]['start']!;
      final end = keepRanges[i]['end']!;
      filterVNodes.add('[0:v]trim=start=$start:end=$end,setpts=PTS-STARTPTS[v$i]');
      filterANodes.add('[0:a]atrim=start=$start:end=$end,asetpts=PTS-STARTPTS[a$i]');
    }

    var concatInputs = '';
    for (var i = 0; i < keepRanges.length; i++) {
      concatInputs += '[v$i][a$i]';
    }

    final concatNode = '${concatInputs}concat=n=${keepRanges.length}:v=1:a=1[v_cut][a_cut]';
    var filterComplex = '${filterVNodes.join('; ')}; ${filterANodes.join('; ')}; $concatNode';

    var mapVideo = '[v_cut]';
    final mapAudio = '[a_cut]';

    // Jika mode hardsub, tambahkan node pembakaran subtitle
    if (mode == 'hardsub') {
      if (shiftedAssPath != null && File(shiftedAssPath).existsSync()) {
        final escapedPath = escapePathForFfmpegFilter(shiftedAssPath);
        filterComplex += '; [v_cut]subtitles=\'$escapedPath\'[v_final]';
        mapVideo = '[v_final]';
      } else if (shiftedSrtPath != null && File(shiftedSrtPath).existsSync()) {
        final escapedPath = escapePathForFfmpegFilter(shiftedSrtPath);
        final forceStyle = fontSize != null && fontSize > 0
            ? ":force_style='Fontsize=$fontSize,Outline=2,Shadow=0'"
            : '';
        filterComplex += '; [v_cut]subtitles=\'$escapedPath\'$forceStyle[v_final]';
        mapVideo = '[v_final]';
      }
    }

    args.addAll([
      '-filter_complex',
      filterComplex,
      '-map',
      mapVideo,
      '-map',
      mapAudio,
      outputPath
    ]);

    return args;
  }

  // Helper parser durasi format HH:MM:SS.xx ke detik
  static double parseFfmpegTime(String timeStr) {
    try {
      final parts = timeStr.trim().split(':');
      if (parts.length < 3) return 0.0;
      final hrs = double.parse(parts[0]);
      final mins = double.parse(parts[1]);
      final secs = double.parse(parts[2]);
      return hrs * 3600 + mins * 60 + secs;
    } catch (_) {
      return 0.0;
    }
  }
}
