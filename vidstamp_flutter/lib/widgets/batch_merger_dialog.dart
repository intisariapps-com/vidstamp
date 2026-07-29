import 'dart:io';
import 'package:flutter/material.dart';
import '../utils/batch_processor.dart';
import '../utils/video_processor.dart';
import '../utils/subtitle_processor.dart';

class BatchMergerDialog extends StatefulWidget {
  const BatchMergerDialog({super.key});

  @override
  State<BatchMergerDialog> createState() => _BatchMergerDialogState();
}

class _BatchMergerDialogState extends State<BatchMergerDialog> {
  final TextEditingController _folderController = TextEditingController();
  List<EpisodeTask> _episodes = [];
  List<bool> _selectedEpisodes = [];

  // Pengaturan ekspor
  bool _mergeToOne = true;
  String _mode = 'softsub';
  int _lineLimit = 45;
  int _fontSize = 18;

  // Status proses berjalan
  bool _isScanning = false;
  bool _isProcessing = false;
  double _totalProgress = 0.0;
  String _currentStatus = '';
  int _completedCount = 0;
  bool _isCompleted = false;
  bool _hasFailed = false;

  final List<String> _supportedExtensions = ['.mkv', '.mp4', '.avi', '.mov', '.m4v'];

  @override
  void dispose() {
    _folderController.dispose();
    super.dispose();
  }

  Future<void> _scanFolder() async {
    final folderPath = _folderController.text.trim();
    if (folderPath.isEmpty) {
      _showSnack('Masukkan path folder terlebih dahulu.', Colors.amber);
      return;
    }

    final dir = Directory(folderPath);
    if (!dir.existsSync()) {
      _showSnack('Folder tidak ditemukan!', Colors.redAccent);
      return;
    }

    setState(() {
      _isScanning = true;
      _episodes = [];
      _selectedEpisodes = [];
    });

    try {
      final List<EpisodeTask> found = [];
      final entries = dir.listSync()
        ..sort((a, b) => a.path.compareTo(b.path));

      for (var entry in entries) {
        if (entry is File) {
          final ext = entry.path.toLowerCase().substring(
                entry.path.length > 4 ? entry.path.length - 4 : 0);
          if (_supportedExtensions.any((e) => entry.path.toLowerCase().endsWith(e))) {
            found.add(EpisodeTask(videoPath: entry.path));
          }
        }
      }

      setState(() {
        _episodes = found;
        _selectedEpisodes = List.filled(found.length, true);
        _isScanning = false;
        _currentStatus = '${found.length} file video ditemukan.';
      });
    } catch (e) {
      setState(() {
        _isScanning = false;
        _currentStatus = 'Gagal memindai folder: $e';
      });
    }
  }

  Future<void> _startBatch() async {
    final selectedTasks = _episodes
        .asMap()
        .entries
        .where((e) => _selectedEpisodes[e.key])
        .map((e) => e.value)
        .toList();

    if (selectedTasks.isEmpty) {
      _showSnack('Pilih minimal satu episode untuk diproses.', Colors.amber);
      return;
    }

    final ffmpegPath = VideoProcessor.getFfmpegPath();
    if (ffmpegPath == null) {
      _showSnack('Biner FFmpeg tidak ditemukan!', Colors.redAccent);
      return;
    }

    // Dapatkan ffprobe (sama dengan ffmpeg tapi diganti nama file)
    String? ffprobePath;
    final ffmpegDir = File(ffmpegPath).parent.path;
    final ffprobeName = Platform.isWindows ? 'ffprobe.exe' : 'ffprobe';
    final localFfprobe = File('$ffmpegDir${Platform.pathSeparator}$ffprobeName');
    if (localFfprobe.existsSync()) {
      ffprobePath = localFfprobe.path;
    } else {
      // Coba dari system path
      final envPath = Platform.environment['PATH'] ?? '';
      final sep = Platform.isWindows ? ';' : ':';
      for (var p in envPath.split(sep)) {
        final f = File('$p${Platform.pathSeparator}$ffprobeName');
        if (f.existsSync()) {
          ffprobePath = f.path;
          break;
        }
      }
    }

    if (ffprobePath == null) {
      _showSnack('Biner ffprobe tidak ditemukan!', Colors.redAccent);
      return;
    }

    setState(() {
      _isProcessing = true;
      _totalProgress = 0.0;
      _completedCount = 0;
      _isCompleted = false;
      _hasFailed = false;
    });

    // Tentukan folder output berdasarkan folder input
    final folderPath = _folderController.text.trim();
    final folderName = Directory(folderPath).path.split(Platform.pathSeparator).last;
    final outputBase = '$folderPath${Platform.pathSeparator}$folderName';

    final List<String> tempCleanVideos = [];
    final List<Map<String, dynamic>> globalSubs = [];
    double accumulatedOffset = 0.0;
    bool anyFailed = false;

    for (var i = 0; i < selectedTasks.length; i++) {
      final task = selectedTasks[i];
      final epName = task.filename;

      setState(() {
        _currentStatus = 'Memproses [${i + 1}/${selectedTasks.length}] $epName...';
        task.status = 'processing';
        // Update episode status di daftar utama jika masih terlihat
      });

      final tempOutput = '$folderPath${Platform.pathSeparator}temp_clean_ep_${i.toString().padLeft(3, '0')}.mp4';

      try {
        final result = await BatchProcessor.processEpisode(
          videoPath: task.videoPath,
          ffmpegPath: ffmpegPath,
          ffprobePath: ffprobePath!,
          tempOutputVideoPath: tempOutput,
          lineLimit: _lineLimit,
          onStatus: (status) {
            if (mounted) {
              setState(() {
                _currentStatus = '[${i + 1}/${selectedTasks.length}] $epName - $status';
              });
            }
          },
        );

        if (result != null) {
          if (_mergeToOne) {
            tempCleanVideos.add(result.tempCleanVideoPath);
            // Offset subtitle episode ini dengan akumulasi offset
            for (var sub in result.shiftedSubtitles) {
              globalSubs.add({
                'start': (sub['start'] as double) + accumulatedOffset,
                'end': (sub['end'] as double) + accumulatedOffset,
                'text': sub['text'],
              });
            }
            accumulatedOffset += result.episodeDuration;
          }
          task.status = 'done';
        } else {
          task.status = 'error';
          task.errorMessage = 'Gagal memproses episode';
          anyFailed = true;
        }
      } catch (e) {
        task.status = 'error';
        task.errorMessage = e.toString();
        anyFailed = true;
      }

      setState(() {
        _completedCount = i + 1;
        _totalProgress = (i + 1) / selectedTasks.length;
      });
    }

    // Concat lossless jika mode mergeToOne
    if (_mergeToOne && tempCleanVideos.isNotEmpty) {
      setState(() {
        _currentStatus = 'Menggabungkan semua episode secara lossless...';
        _totalProgress = 0.95;
      });

      final outputVideo = '${outputBase}_clean.mp4';
      final concatSuccess = await BatchProcessor.concatEpisodesLossless(
        tempVideoPaths: tempCleanVideos,
        outputVideoPath: outputVideo,
        ffmpegPath: ffmpegPath,
      );

      if (!concatSuccess) anyFailed = true;

      // Tulis subtitle global
      if (globalSubs.isNotEmpty) {
        final outputSrt = '${outputBase}_clean.srt';
        BatchProcessor.buildGlobalSubtitleSrt(
          globalSubs: globalSubs,
          outputSrtPath: outputSrt,
        );
      }

      // Bersihkan berkas sementara
      setState(() { _currentStatus = 'Membersihkan berkas sementara...'; });
      for (var p in tempCleanVideos) {
        try { File(p).deleteSync(); } catch (_) {}
      }
    }

    setState(() {
      _isProcessing = false;
      _isCompleted = true;
      _hasFailed = anyFailed;
      _totalProgress = 1.0;
      _currentStatus = anyFailed
          ? 'Proses selesai dengan beberapa kegagalan.'
          : 'Semua episode berhasil diproses dan digabungkan!';
    });
  }

  void _showSnack(String msg, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: color, duration: const Duration(seconds: 2)),
    );
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'done': return Colors.greenAccent;
      case 'error': return Colors.redAccent;
      case 'processing': return Colors.amberAccent;
      default: return Colors.grey;
    }
  }

  IconData _statusIcon(String status) {
    switch (status) {
      case 'done': return Icons.check_circle_outline;
      case 'error': return Icons.error_outline;
      case 'processing': return Icons.sync;
      default: return Icons.radio_button_unchecked;
    }
  }

  @override
  Widget build(BuildContext context) {
    final selectedCount = _selectedEpisodes.where((s) => s).length;

    return Dialog(
      backgroundColor: const Color(0xFF0E0E1F),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      insetPadding: const EdgeInsets.symmetric(horizontal: 40, vertical: 32),
      child: SizedBox(
        width: 740,
        height: 680,
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header
              Row(
                children: [
                  const Icon(Icons.movie_creation_outlined, color: Colors.indigoAccent, size: 22),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      'Batch Merger Wizard — Penggabungan Massal Episode',
                      style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                  if (!_isProcessing)
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close, color: Colors.grey, size: 20),
                    ),
                ],
              ),
              const SizedBox(height: 20),

              // Input folder
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _folderController,
                      enabled: !_isProcessing,
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                      decoration: InputDecoration(
                        hintText: 'Masukkan path folder episode (contoh: E:\\ANIME\\SAO S1)...',
                        hintStyle: const TextStyle(color: Colors.grey, fontSize: 12),
                        filled: true,
                        fillColor: const Color(0xFF16162A),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: Color(0xFF25254A)),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: Colors.indigoAccent),
                        ),
                        disabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: Color(0xFF25254A)),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton.icon(
                    onPressed: _isProcessing ? null : _scanFolder,
                    icon: _isScanning
                        ? const SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : const Icon(Icons.folder_open, size: 18),
                    label: const Text('Pindai Folder'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1A73E8),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Pengaturan
              if (!_isProcessing && _episodes.isEmpty)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF16162A),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFF25254A)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Pengaturan Ekspor:', style: TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Checkbox(
                            value: _mergeToOne,
                            onChanged: (v) => setState(() => _mergeToOne = v!),
                            activeColor: Colors.indigoAccent,
                          ),
                          const Text('Gabungkan menjadi 1 file utama', style: TextStyle(color: Colors.white, fontSize: 13)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Text('Mode Subtitle: ', style: TextStyle(color: Colors.grey, fontSize: 12)),
                          Radio<String>(
                            value: 'softsub',
                            groupValue: _mode,
                            activeColor: Colors.indigoAccent,
                            onChanged: (v) => setState(() => _mode = v!),
                          ),
                          const Text('Softsub', style: TextStyle(color: Colors.white, fontSize: 12)),
                          const SizedBox(width: 8),
                          Radio<String>(
                            value: 'hardsub',
                            groupValue: _mode,
                            activeColor: Colors.indigoAccent,
                            onChanged: (v) => setState(() => _mode = v!),
                          ),
                          const Text('Hardsub', style: TextStyle(color: Colors.white, fontSize: 12)),
                        ],
                      ),
                    ],
                  ),
                ),

              // Daftar Episode
              if (_episodes.isNotEmpty)
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Kontrol pilih semua
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Checkbox(
                                value: selectedCount == _episodes.length,
                                tristate: true,
                                onChanged: _isProcessing
                                    ? null
                                    : (v) {
                                        setState(() {
                                          final val = v ?? false;
                                          _selectedEpisodes = List.filled(_episodes.length, val);
                                        });
                                      },
                                activeColor: Colors.indigoAccent,
                              ),
                              Text(
                                'Pilih Semua ($selectedCount/${_episodes.length} dipilih)',
                                style: const TextStyle(color: Colors.grey, fontSize: 12),
                              ),
                            ],
                          ),
                          Row(
                            children: [
                              Checkbox(
                                value: _mergeToOne,
                                onChanged: _isProcessing ? null : (v) => setState(() => _mergeToOne = v!),
                                activeColor: Colors.indigoAccent,
                              ),
                              const Text('Gabungkan 1 file', style: TextStyle(color: Colors.grey, fontSize: 12)),
                            ],
                          ),
                        ],
                      ),

                      // List episode
                      Expanded(
                        child: Container(
                          decoration: BoxDecoration(
                            color: const Color(0xFF16162A),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: const Color(0xFF25254A)),
                          ),
                          child: ListView.separated(
                            padding: const EdgeInsets.all(8),
                            itemCount: _episodes.length,
                            separatorBuilder: (_, __) => const Divider(color: Color(0xFF25254A), height: 1),
                            itemBuilder: (context, i) {
                              final ep = _episodes[i];
                              return Row(
                                children: [
                                  Checkbox(
                                    value: _selectedEpisodes[i],
                                    onChanged: _isProcessing
                                        ? null
                                        : (v) => setState(() => _selectedEpisodes[i] = v!),
                                    activeColor: Colors.indigoAccent,
                                  ),
                                  Icon(
                                    _statusIcon(ep.status),
                                    color: _statusColor(ep.status),
                                    size: 16,
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      ep.filename,
                                      style: const TextStyle(color: Colors.white, fontSize: 12),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  if (ep.status == 'error')
                                    Padding(
                                      padding: const EdgeInsets.only(right: 8),
                                      child: Text(
                                        ep.errorMessage ?? 'Error',
                                        style: const TextStyle(color: Colors.redAccent, fontSize: 10),
                                      ),
                                    ),
                                ],
                              );
                            },
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 16),

              // Progress bar (hanya saat memproses)
              if (_isProcessing || _isCompleted) ...[
                LinearProgressIndicator(
                  value: _totalProgress,
                  backgroundColor: Colors.white12,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    _hasFailed ? Colors.redAccent : Colors.indigoAccent,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        _currentStatus,
                        style: TextStyle(
                          color: _hasFailed ? Colors.redAccent : Colors.grey,
                          fontSize: 12,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(
                      '${(_totalProgress * 100).toStringAsFixed(0)}%',
                      style: TextStyle(
                        color: _hasFailed ? Colors.redAccent : Colors.indigoAccent,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
              ],

              // Tombol aksi bawah
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (!_isProcessing && !_isCompleted)
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Batal', style: TextStyle(color: Colors.grey)),
                    ),
                  const SizedBox(width: 8),
                  if (!_isProcessing && !_isCompleted)
                    ElevatedButton.icon(
                      onPressed: _episodes.isEmpty ? null : _startBatch,
                      icon: const Icon(Icons.merge_type_outlined, size: 18),
                      label: const Text('Mulai Proses Massal'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFE94560),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                  if (_isCompleted)
                    ElevatedButton.icon(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.check, size: 18),
                      label: const Text('Selesai'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.indigoAccent,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
