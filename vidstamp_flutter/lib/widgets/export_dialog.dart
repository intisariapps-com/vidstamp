import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import '../utils/video_processor.dart';

class ExportProgressDialog extends StatefulWidget {
  final String videoPath;
  final List<Map<String, double>> keepRanges;
  final String outputPath;
  final String mode; // 'softsub' atau 'hardsub'
  final String? shiftedAssPath;
  final String? shiftedSrtPath;
  final int? fontSize;
  final double totalKeepDuration;

  const ExportProgressDialog({
    super.key,
    required this.videoPath,
    required this.keepRanges,
    required this.outputPath,
    required this.mode,
    this.shiftedAssPath,
    this.shiftedSrtPath,
    this.fontSize,
    required this.totalKeepDuration,
  });

  @override
  State<ExportProgressDialog> createState() => _ExportProgressDialogState();
}

class _ExportProgressDialogState extends State<ExportProgressDialog> {
  Process? _process;
  double _progress = 0.0;
  String _statusMessage = "Menyiapkan proses rendering...";
  bool _isCompleted = false;
  bool _isFailed = false;
  String _errorMessage = "";

  @override
  void initState() {
    super.initState();
    _startExport();
  }

  Future<void> _startExport() async {
    final ffmpegPath = VideoProcessor.getFfmpegPath();
    if (ffmpegPath == null) {
      setState(() {
        _isFailed = true;
        _errorMessage = "Gagal menemukan biner FFmpeg di sistem.";
      });
      return;
    }

    final args = VideoProcessor.buildFfmpegArgs(
      videoPath: widget.videoPath,
      keepRanges: widget.keepRanges,
      outputPath: widget.outputPath,
      mode: widget.mode,
      shiftedAssPath: widget.shiftedAssPath,
      shiftedSrtPath: widget.shiftedSrtPath,
      fontSize: widget.fontSize,
    );

    try {
      final proc = await Process.start(ffmpegPath, args);
      _process = proc;

      setState(() {
        _statusMessage = "Mengekspor video (FFmpeg)...";
      });

      final timeRegex = RegExp(r"time=(\d{2}):(\d{2}):(\d{2})[.,](\d{2})");

      proc.stderr
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((line) {
        final match = timeRegex.firstMatch(line);
        if (match != null && widget.totalKeepDuration > 0) {
          final h = match.group(1)!;
          final m = match.group(2)!;
          final s = match.group(3)!;
          final ms = match.group(4)!;
          
          final processedSecs = double.parse(h) * 3600 +
              double.parse(m) * 60 +
              double.parse(s) +
              double.parse(ms) / 100.0;

          if (mounted) {
            setState(() {
              _progress = (processedSecs / widget.totalKeepDuration).clamp(0.0, 1.0);
            });
          }
        }
      });

      final exitCode = await proc.exitCode;
      if (exitCode == 0) {
        if (mounted) {
          setState(() {
            _isCompleted = true;
            _progress = 1.0;
            _statusMessage = "Video berhasil diekspor dengan sukses!";
          });
        }
      } else {
        if (mounted) {
          setState(() {
            _isFailed = true;
            _errorMessage = "FFmpeg keluar dengan kode error: $exitCode";
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isFailed = true;
          _errorMessage = e.toString();
        });
      }
    }
  }

  void _cancelExport() {
    if (_process != null) {
      _process!.kill();
      _showSnackbar("Proses ekspor dibatalkan oleh pengguna.");
    }
    Navigator.pop(context, false);
  }

  void _showSnackbar(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.amber),
    );
  }

  @override
  Widget build(BuildContext context) {
    final percent = (_progress * 100).toStringAsFixed(1);
    
    return WillPopScope(
      onWillPop: () async => false, // Kunci tombol back agar tidak menutup manual
      child: AlertDialog(
        backgroundColor: const Color(0xFF16162A),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        title: const Text(
          "Mengekspor Adegan Bersih",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
        ),
        content: SizedBox(
          width: 320,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                _statusMessage,
                style: const TextStyle(color: Colors.grey, fontSize: 13),
              ),
              const SizedBox(height: 16),
              
              if (!_isFailed) ...[
                LinearProgressIndicator(
                  value: _progress,
                  backgroundColor: Colors.white12,
                  valueColor: const AlwaysStoppedAnimation<Color>(Colors.indigoAccent),
                ),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: Text(
                    "$percent%",
                    style: const TextStyle(color: Colors.indigoAccent, fontSize: 13, fontWeight: FontWeight.bold),
                  ),
                ),
              ] else ...[
                Text(
                  "Error: $_errorMessage",
                  style: const TextStyle(color: Colors.redAccent, fontSize: 13),
                ),
              ],
            ],
          ),
        ),
        actions: [
          if (!_isCompleted && !_isFailed)
            TextButton(
              onPressed: _cancelExport,
              child: const Text("Batal", style: TextStyle(color: Colors.redAccent)),
            ),
          if (_isCompleted || _isFailed)
            ElevatedButton(
              onPressed: () => Navigator.pop(context, _isCompleted),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.indigoAccent),
              child: const Text("Selesai"),
            ),
        ],
      ),
    );
  }
}
