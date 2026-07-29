import 'dart:io';

class SubtitleProcessor {
  // 1. Detektor Gambar Vektor ASS
  static bool isVectorDrawing(String text) {
    final cleanText = text.trim();
    if (cleanText.isEmpty) return false;
    final regex = RegExp(r'^\s*m\s+-?\d+\s+-?\d+', caseSensitive: false);
    return regex.hasMatch(cleanText);
  }

  // 2. Detektor Gaya Non-dialog
  static bool isBlacklistedStyle(String style) {
    final styleLower = style.toLowerCase();
    final blacklist = ['romaji', 'kanji', 'karaoke', 'draw', 'drawing'];
    for (var kw in blacklist) {
      if (styleLower.contains(kw)) return true;
    }
    return false;
  }

  // 3. Pembersih Tag ASS ke SRT Polos
  static String cleanAssTextToSrt(String assText) {
    var text = assText;
    // Hapus seluruh kurung kurawal ASS {\...}
    text = text.replaceAll(RegExp(r'\{[^}]*\}'), '');
    // Ganti \N (line break ASS) menjadi \n
    text = text.replaceAll(RegExp(r'\\N', caseSensitive: false), '\n');
    // Hapus spaces ganda
    text = text.replaceAll(RegExp(r' +'), ' ');
    return text.trim();
  }

  // 4. Pembersih Teks SRT
  static String cleanSrtText(String srtText) {
    var text = srtText;
    // Hapus tag HTML seperti <i>, <font>, dll
    text = text.replaceAll(RegExp(r'<[^>]*>'), '');
    text = text.replaceAll(RegExp(r'\{[^}]*\}'), '');
    // Normalkan line breaks
    text = text.replaceAll('\r\n', '\n');
    text = text.replaceAll(RegExp(r'\n\s*\n'), '\n');
    return text.trim();
  }

  // 5. Pembatas Panjang Karakter Per Baris
  static String wrapTextByCharLimit(String text, int limit) {
    if (text.isEmpty || limit <= 0) return text;
    final lines = text.split('\n');
    final List<String> wrappedLines = [];

    for (var line in lines) {
      if (line.length <= limit) {
        wrappedLines.add(line);
        continue;
      }
      final words = line.split(' ');
      final List<String> currentLineWords = [];
      int currentLength = 0;

      for (var word in words) {
        if (currentLength + word.length + (currentLineWords.isNotEmpty ? 1 : 0) <= limit) {
          currentLineWords.add(word);
          currentLength += word.length + (currentLineWords.length > 1 ? 1 : 0);
        } else {
          if (currentLineWords.isNotEmpty) {
            wrappedLines.add(currentLineWords.join(' '));
          }
          currentLineWords.clear();
          currentLineWords.add(word);
          currentLength = word.length;
        }
      }
      if (currentLineWords.isNotEmpty) {
        wrappedLines.add(currentLineWords.join(' '));
      }
    }
    return wrappedLines.join('\n');
  }

  // Helper parser waktu ASS (format: h:mm:ss.xx) ke detik
  static double assTimeToSeconds(String timeStr) {
    final parts = timeStr.trim().split(':');
    if (parts.length < 3) return 0.0;
    final hrs = double.parse(parts[0]);
    final mins = double.parse(parts[1]);
    final secs = double.parse(parts[2]);
    return hrs * 3600 + mins * 60 + secs;
  }

  // Helper format detik ke waktu ASS (format: h:mm:ss.xx)
  static String secondsToAssTime(double totalSecs) {
    final hrs = (totalSecs / 3600).floor();
    final mins = ((totalSecs % 3600) / 60).floor();
    final secs = totalSecs % 60;
    
    final hrsStr = hrs.toString();
    final minsStr = mins.toString().padLeft(2, '0');
    final secsStr = secs.toStringAsFixed(2).padLeft(5, '0');
    return '$hrsStr:$minsStr:$secsStr';
  }

  // Helper parser waktu SRT (format: hh:mm:ss,xxx) ke detik
  static double srtTimeToSeconds(String timeStr) {
    final cleaned = timeStr.trim().replaceAll(',', '.');
    final parts = cleaned.split(':');
    if (parts.length < 3) return 0.0;
    final hrs = double.parse(parts[0]);
    final mins = double.parse(parts[1]);
    final secs = double.parse(parts[2]);
    return hrs * 3600 + mins * 60 + secs;
  }

  // Helper format detik ke waktu SRT (format: hh:mm:ss,xxx)
  static String secondsToSrtTime(double totalSecs) {
    final hrs = (totalSecs / 3600).floor();
    final mins = ((totalSecs % 3600) / 60).floor();
    final secs = (totalSecs % 60).floor();
    final ms = ((totalSecs - totalSecs.floor()) * 1000).round();
    
    final hrsStr = hrs.toString().padLeft(2, '0');
    final minsStr = mins.toString().padLeft(2, '0');
    final secsStr = secs.toString().padLeft(2, '0');
    final msStr = ms.toString().padLeft(3, '0');
    return '$hrsStr:$minsStr:$secsStr,$msStr';
  }

  // 6. Parsing dan Pembersihan Berkas ASS
  static List<Map<String, dynamic>> parseAndCleanAssToSrtSubs(String assPath, List<Map<String, double>> keepRanges) {
    final List<Map<String, dynamic>> subsList = [];
    final file = File(assPath);
    if (!file.existsSync()) return subsList;

    final lines = file.readAsLinesSync();
    for (var line in lines) {
      if (!line.startsWith('Dialogue:')) continue;
      
      // Parse Dialogue Line
      final rest = line.substring(9).trim();
      final parts = rest.split(',');
      if (parts.length < 10) continue;
      
      final startStr = parts[1];
      final endStr = parts[2];
      final style = parts[3];
      final text = parts.sublist(9).join(',');

      if (isBlacklistedStyle(style)) continue;

      final cleanTxt = cleanAssTextToSrt(text);
      if (cleanTxt.isEmpty || isVectorDrawing(cleanTxt)) continue;

      final startSec = assTimeToSeconds(startStr);
      final endSec = assTimeToSeconds(endStr);

      // Filter Durasi Minimum 300ms
      if (endSec - startSec < 0.3) continue;

      // Cari segment keep yang memuat startSec
      double? mappedStart;
      double? mappedEnd;
      double accKeepDuration = 0.0;

      for (var range in keepRanges) {
        final kStart = range['start']!;
        final kEnd = range['end']!;
        if (startSec >= kStart && startSec < kEnd) {
          mappedStart = (startSec - kStart) + accKeepDuration;
          mappedEnd = (endSec - kStart) + accKeepDuration;
          break;
        }
        accKeepDuration += (kEnd - kStart);
      }

      if (mappedStart != null && mappedEnd != null) {
        subsList.add({
          'start': mappedStart,
          'end': mappedEnd,
          'text': cleanTxt,
        });
      }
    }

    return subsList;
  }

  // 7. Deduplikasi OCR & Spam Subtitle
  static List<Map<String, dynamic>> mergeDuplicateOcrSubtitles(List<Map<String, dynamic>> subs) {
    if (subs.isEmpty) return [];

    // Urutkan berdasarkan waktu mulai
    subs.sort((a, b) => (a['start'] as double).compareTo(b['start'] as double));

    final List<Map<String, dynamic>> merged = [];
    
    for (var current in subs) {
      if (merged.isEmpty) {
        merged.add(Map.from(current));
        continue;
      }

      final last = merged.last;
      final lastText = last['text'].toString().toLowerCase().trim();
      final currText = current['text'].toString().toLowerCase().trim();

      // Cek apakah teks identik
      if (lastText == currText) {
        final lastEnd = last['end'] as double;
        final currStart = current['start'] as double;

        // Cari adegan tumpang tindih atau jeda <= 2.5 detik
        if (currStart <= lastEnd || (currStart - lastEnd) <= 2.5) {
          // Gabungkan waktu (ambil end yang paling besar)
          final currEnd = current['end'] as double;
          if (currEnd > lastEnd) {
            last['end'] = currEnd;
          }
          continue;
        }
      }
      merged.add(Map.from(current));
    }
    return merged;
  }

  // 8. Cut & Shift SRT Utama
  static bool cutAndShiftSrt(
    String inputSrtPath,
    List<Map<String, double>> keepRanges,
    String outputSrtPath, {
    int? lineLimit,
    String? inputAssPath,
  }) {
    List<Map<String, dynamic>> subsList = [];

    // Jika ada file ASS, gunakan parser ASS pintar
    if (inputAssPath != null && File(inputAssPath).existsSync()) {
      subsList = parseAndCleanAssToSrtSubs(inputAssPath, keepRanges);
    } else if (File(inputSrtPath).existsSync()) {
      // Fallback ke parser SRT
      try {
        final content = File(inputSrtPath).readAsStringSync();
        final blocks = content.trim().split(RegExp(r'\n\s*\n'));

        for (var block in blocks) {
          final lines = block.trim().split('\n');
          if (lines.length >= 2) {
            int tsLineIdx = -1;
            for (var i = 0; i < lines.length; i++) {
              if (lines[i].contains('-->')) {
                tsLineIdx = i;
                break;
              }
            }

            if (tsLineIdx != -1) {
              final dialogueLines = lines.sublist(tsLineIdx + 1);
              final cleanText = cleanSrtText(dialogueLines.join('\n'));

              if (cleanText.isNotEmpty) {
                final tsLine = lines[tsLineIdx];
                final parts = tsLine.split('-->');
                if (parts.length == 2) {
                  final startSec = srtTimeToSeconds(parts[0]);
                  final endSec = srtTimeToSeconds(parts[1]);

                  double? mappedStart;
                  double? mappedEnd;
                  double accKeepDuration = 0.0;

                  for (var range in keepRanges) {
                    final kStart = range['start']!;
                    final kEnd = range['end']!;
                    if (startSec >= kStart && startSec < kEnd) {
                      mappedStart = (startSec - kStart) + accKeepDuration;
                      mappedEnd = (endSec - kStart) + accKeepDuration;
                      break;
                    }
                    accKeepDuration += (kEnd - kStart);
                  }

                  if (mappedStart != null && mappedEnd != null) {
                    subsList.add({
                      'start': mappedStart,
                      'end': mappedEnd,
                      'text': cleanText,
                    });
                  }
                }
              }
            }
          }
        }
      } catch (e) {
        print('Gagal memproses SRT input: $e');
      }
    }

    // Terapkan batas baris & buang sisa vektor
    final List<Map<String, dynamic>> processedSubs = [];
    for (var sub in subsList) {
      var txt = cleanSrtText(sub['text']);
      if (lineLimit != null && lineLimit > 0) {
        txt = wrapTextByCharLimit(txt, lineLimit);
      }
      if (txt.isNotEmpty && !isVectorDrawing(txt)) {
        processedSubs.add({
          'start': sub['start'],
          'end': sub['end'],
          'text': txt,
        });
      }
    }

    // Jalankan deduplikasi OCR
    final deduplicated = mergeDuplicateOcrSubtitles(processedSubs);

    // Konversi kembali ke format SRT
    try {
      final List<String> shiftedBlocks = [];
      for (var i = 0; i < deduplicated.length; i++) {
        final sub = deduplicated[i];
        final newTs = '${secondsToSrtTime(sub['start'])} --> ${secondsToSrtTime(sub['end'])}';
        shiftedBlocks.add('${i + 1}\n$newTs\n${sub['text']}');
      }

      File(outputSrtPath).writeAsStringSync(shiftedBlocks.join('\n\n'));
      return true;
    } catch (e) {
      print('Gagal menulis file SRT output: $e');
      return false;
    }
  }

  // 9. Cut & Shift ASS Utama (untuk Hardsub gaya native)
  static bool cutAndShiftAss(String inputAssPath, List<Map<String, double>> keepRanges, String outputAssPath) {
    final file = File(inputAssPath);
    if (!file.existsSync()) return false;

    try {
      final lines = file.readAsLinesSync();
      final List<String> shiftedLines = [];

      for (var line in lines) {
        if (!line.startsWith('Dialogue:')) {
          shiftedLines.add(line);
          continue;
        }

        final rest = line.substring(9).trim();
        final parts = rest.split(',');
        if (parts.length < 10) {
          shiftedLines.add(line);
          continue;
        }

        final layer = parts[0];
        final startStr = parts[1];
        final endStr = parts[2];
        final style = parts[3];
        final name = parts[4];
        final marginL = parts[5];
        final marginR = parts[6];
        final marginV = parts[7];
        final effect = parts[8];
        final text = parts.sublist(9).join(',');

        if (isBlacklistedStyle(style)) continue;

        final cleanTxt = cleanAssTextToSrt(text);
        if (cleanTxt.isEmpty || isVectorDrawing(cleanTxt)) continue;

        final startSec = assTimeToSeconds(startStr);
        final endSec = assTimeToSeconds(endStr);

        if (endSec - startSec < 0.3) continue;

        double? mappedStart;
        double? mappedEnd;
        double accKeepDuration = 0.0;

        for (var range in keepRanges) {
          final kStart = range['start']!;
          final kEnd = range['end']!;
          if (startSec >= kStart && startSec < kEnd) {
            mappedStart = (startSec - kStart) + accKeepDuration;
            mappedEnd = (endSec - kStart) + accKeepDuration;
            break;
          }
          accKeepDuration += (kEnd - kStart);
        }

        if (mappedStart != null && mappedEnd != null) {
          final newStartStr = secondsToAssTime(mappedStart);
          final newEndStr = secondsToAssTime(mappedEnd);
          final newLine = 'Dialogue: $layer,$newStartStr,$newEndStr,$style,$name,$marginL,$marginR,$marginV,$effect,$text';
          shiftedLines.add(newLine);
        }
      }

      File(outputAssPath).writeAsStringSync(shiftedLines.join('\n'));
      return true;
    } catch (e) {
      print('Gagal menyelaraskan subtitel ASS: $e');
      return false;
    }
  }
}
