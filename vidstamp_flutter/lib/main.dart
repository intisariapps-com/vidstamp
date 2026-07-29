import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';
import 'models/scene_note.dart';
import 'widgets/video_player_panel.dart';
import 'widgets/notes_panel.dart';
import 'package:uuid/uuid.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  MediaKit.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VidStamp Desktop',
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.indigo,
        scaffoldBackgroundColor: const Color(0xFF090916),
        fontFamily: 'Segoe UI',
      ),
      home: const MainSplitScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class MainSplitScreen extends StatefulWidget {
  const MainSplitScreen({super.key});

  @override
  State<MainSplitScreen> createState() => _MainSplitScreenState();
}

class _MainSplitScreenState extends State<MainSplitScreen> {
  late final Player _player;
  late final VideoController _controller;
  final TextEditingController _pathController = TextEditingController();
  
  final List<SceneNote> _notes = [];
  String _currentVideoPath = "";
  final _uuid = const Uuid();

  // State perekaman toggle
  Duration? _pendingSceneStart;
  Duration? _pendingOpeningStart;
  Duration? _pendingClosingStart;

  // State Auto-Skip
  bool _autoSkipEnabled = true;
  Duration? _opStart;
  Duration? _opEnd;
  Duration? _edStart;
  Duration? _edEnd;

  @override
  void initState() {
    super.initState();
    _player = Player();
    _controller = VideoController(_player);

    // Dengarkan posisi waktu untuk auto-skip
    _player.stream.position.listen((pos) {
      _checkAutoSkip(pos);
    });

    // Default placeholder path
    _pathController.text = r"E:\ANIME\Sword Art Online\Sword Art Online S1\Sword Art Online S1\[Kusonime] Sword Art Online BD - 01.mkv";
  }

  @override
  void dispose() {
    _player.dispose();
    _pathController.dispose();
    super.dispose();
  }

  void _checkAutoSkip(Duration pos) {
    if (!_autoSkipEnabled) return;

    // Lompat Opening
    if (_opStart != null && _opEnd != null) {
      if (pos >= _opStart! && pos < _opEnd!) {
        _player.seek(_opEnd!);
        _showSnackbar('Melompati Opening otomatis...', Colors.indigoAccent);
        return;
      }
    }

    // Lompat Ending
    if (_edStart != null && _edEnd != null) {
      if (pos >= _edStart! && pos < _edEnd!) {
        _player.seek(_edEnd!);
        _showSnackbar('Melompati Ending otomatis...', Colors.indigoAccent);
        return;
      }
    }
  }

  String? _getFfprobePath() {
    final envPath = Platform.environment['PATH'] ?? '';
    final separator = Platform.isWindows ? ';' : ':';
    final paths = envPath.split(separator);
    final ffprobeName = Platform.isWindows ? 'ffprobe.exe' : 'ffprobe';

    for (var path in paths) {
      final file = File('$path${Platform.pathSeparator}$ffprobeName');
      if (file.existsSync()) {
        return file.path;
      }
    }

    final localBin = Directory(Directory.current.path).parent.path;
    final fallbackFile = File(
      Platform.isWindows
          ? '$localBin${Platform.pathSeparator}bin${Platform.pathSeparator}win${Platform.pathSeparator}ffprobe.exe'
          : '$localBin${Platform.pathSeparator}bin${Platform.pathSeparator}mac${Platform.pathSeparator}ffprobe',
    );

    if (fallbackFile.existsSync()) {
      return fallbackFile.path;
    }

    return null;
  }

  Future<void> _detectChapters(String videoPath) async {
    setState(() {
      _opStart = null;
      _opEnd = null;
      _edStart = null;
      _edEnd = null;
    });

    if (!videoPath.toLowerCase().endsWith('.mkv')) return;

    try {
      final ffprobePath = _getFfprobePath();
      if (ffprobePath == null) {
        print('ffprobe tidak ditemukan, deteksi bab dibatalkan.');
        return;
      }

      final result = await Process.run(ffprobePath, [
        '-v', 'error',
        '-show_chapters',
        '-print_format', 'json',
        videoPath,
      ]);

      if (result.exitCode == 0) {
        final jsonMap = json.decode(result.stdout as String);
        final chapters = jsonMap['chapters'] as List?;
        if (chapters != null) {
          Duration? localOpStart;
          Duration? localOpEnd;
          Duration? localEdStart;
          Duration? localEdEnd;

          for (var chapter in chapters) {
            final start = double.parse(chapter['start_time'].toString());
            final end = double.parse(chapter['end_time'].toString());
            final tags = chapter['tags'] as Map?;
            if (tags != null) {
              final title = tags['title'].toString().toLowerCase();
              if (title.contains('op') || title.contains('opening') || title.contains('intro')) {
                localOpStart = Duration(milliseconds: (start * 1000).toInt());
                localOpEnd = Duration(milliseconds: (end * 1000).toInt());
              } else if (title.contains('ed') || title.contains('ending') || title.contains('outro')) {
                localEdStart = Duration(milliseconds: (start * 1000).toInt());
                localEdEnd = Duration(milliseconds: (end * 1000).toInt());
              }
            }
          }

          if (mounted) {
            setState(() {
              _opStart = localOpStart;
              _opEnd = localOpEnd;
              _edStart = localEdStart;
              _edEnd = localEdEnd;
            });
            if (_opStart != null || _edStart != null) {
              _showSnackbar('Metadata bab MKV terdeteksi otomatis!', Colors.indigoAccent);
            }
          }
        }
      }
    } catch (e) {
      print('Gagal mendeteksi bab: $e');
    }
  }

  void _loadVideo() {
    final path = _pathController.text.trim();
    if (path.isEmpty) return;

    final file = File(path);
    if (file.existsSync()) {
      setState(() {
        _currentVideoPath = path;
        _notes.clear(); // Bersihkan notes untuk video baru
        _pendingSceneStart = null;
        _pendingOpeningStart = null;
        _pendingClosingStart = null;
      });
      _player.open(Media(file.path));
      _showSnackbar('Berhasil memuat video: ${file.path.split(Platform.pathSeparator).last}', Colors.green);
      _detectChapters(path); // Panggil pendeteksi bab otomatis
    } else {
      _showSnackbar('File video tidak ditemukan!', Colors.redAccent);
    }
  }

  void _showSnackbar(String message, Color color) {
    ScaffoldMessenger.of(context).clearSnackBars();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  // Aksi perekam adegan
  void _recordScene() {
    if (_currentVideoPath.isEmpty) {
      _showSnackbar('Buka video terlebih dahulu sebelum merekam!', Colors.amber);
      return;
    }
    final currentPos = _player.state.position;
    if (_pendingSceneStart == null) {
      setState(() => _pendingSceneStart = currentPos);
      _showSnackbar('Mulai merekam adegan pada ${SceneNote.formatDuration(currentPos)}...', Colors.indigoAccent);
    } else {
      final start = _pendingSceneStart!;
      setState(() {
        _notes.add(SceneNote(
          id: _uuid.v4(),
          startTime: start,
          endTime: currentPos,
          note: 'Catatan adegan baru...',
        ));
        _pendingSceneStart = null;
      });
      _showSnackbar('Adegan ditambahkan!', Colors.green);
    }
  }

  void _recordOpening() {
    if (_currentVideoPath.isEmpty) return;
    final currentPos = _player.state.position;
    if (_pendingOpeningStart == null) {
      setState(() => _pendingOpeningStart = currentPos);
      _showSnackbar('Mulai merekam Opening pada ${SceneNote.formatDuration(currentPos)}...', Colors.amberAccent);
    } else {
      final start = _pendingOpeningStart!;
      setState(() {
        _notes.add(SceneNote(
          id: _uuid.v4(),
          startTime: start,
          endTime: currentPos,
          note: 'Opening (OP)',
        ));
        _pendingOpeningStart = null;
      });
      _showSnackbar('Opening ditambahkan!', Colors.green);
    }
  }

  void _recordClosing() {
    if (_currentVideoPath.isEmpty) return;
    final currentPos = _player.state.position;
    if (_pendingClosingStart == null) {
      setState(() => _pendingClosingStart = currentPos);
      _showSnackbar('Mulai merekam Closing pada ${SceneNote.formatDuration(currentPos)}...', Colors.greenAccent);
    } else {
      final start = _pendingClosingStart!;
      setState(() {
        _notes.add(SceneNote(
          id: _uuid.v4(),
          startTime: start,
          endTime: currentPos,
          note: 'Closing (ED)',
        ));
        _pendingClosingStart = null;
      });
      _showSnackbar('Closing ditambahkan!', Colors.green);
    }
  }

  // Ekspor Catatan
  void _exportToTxt() {
    if (_notes.isEmpty) {
      _showSnackbar('Belum ada catatan untuk diekspor!', Colors.amber);
      return;
    }
    
    try {
      final baseName = _currentVideoPath.substring(0, _currentVideoPath.lastIndexOf('.'));
      final targetPath = '${baseName}_catatan_adegan.txt';
      final file = File(targetPath);
      
      final buffer = StringBuffer();
      buffer.writeln('=== CATATAN ADEGAN VIDSTAMP ===');
      buffer.writeln('Berkas Video: $_currentVideoPath');
      buffer.writeln('Tanggal: ${DateTime.now().toLocal()}\n');
      
      for (var note in _notes) {
        buffer.writeln('[${SceneNote.formatDuration(note.startTime)} --> ${SceneNote.formatDuration(note.endTime)}]');
        buffer.writeln('${note.note}\n');
      }
      
      file.writeAsStringSync(buffer.toString());
      _showSnackbar('Catatan berhasil diekspor ke .txt!', Colors.green);
    } catch (e) {
      _showSnackbar('Gagal mengekspor file: $e', Colors.redAccent);
    }
  }

  void _exportToSrt() {
    if (_notes.isEmpty) {
      _showSnackbar('Belum ada catatan untuk diekspor!', Colors.amber);
      return;
    }
    
    try {
      final baseName = _currentVideoPath.substring(0, _currentVideoPath.lastIndexOf('.'));
      final targetPath = '${baseName}_catatan_adegan.srt';
      final file = File(targetPath);
      
      final buffer = StringBuffer();
      for (var i = 0; i < _notes.length; i++) {
        final note = _notes[i];
        final startSrt = SceneNote.formatDuration(note.startTime).replaceFirst('.', ',');
        final endSrt = SceneNote.formatDuration(note.endTime).replaceFirst('.', ',');
        
        buffer.writeln('${i + 1}');
        buffer.writeln('$startSrt --> $endSrt');
        buffer.writeln('${note.note}\n');
      }
      
      file.writeAsStringSync(buffer.toString().trim());
      _showSnackbar('Catatan berhasil diekspor ke .srt!', Colors.green);
    } catch (e) {
      _showSnackbar('Gagal mengekspor file: $e', Colors.redAccent);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Focus(
        autofocus: true,
        onKeyEvent: (node, event) {
          // Pengaman Fokus Pengetikan: Abaikan hotkey jika kursor aktif di input teks
          final primaryFocus = FocusManager.instance.primaryFocus;
          if (primaryFocus != null && primaryFocus.context != null) {
            final isEditable = primaryFocus.context!.findAncestorWidgetOfExactType<EditableText>() != null;
            if (isEditable) {
              return KeyEventResult.ignored;
            }
          }

          if (event is KeyDownEvent) {
            final isCtrl = HardwareKeyboard.instance.isControlPressed ||
                HardwareKeyboard.instance.isMetaPressed;
            
            if (isCtrl) {
              if (event.logicalKey == LogicalKeyboardKey.keyR) {
                _recordScene();
                return KeyEventResult.handled;
              } else if (event.logicalKey == LogicalKeyboardKey.keyO) {
                _recordOpening();
                return KeyEventResult.handled;
              } else if (event.logicalKey == LogicalKeyboardKey.keyC) {
                _recordClosing();
                return KeyEventResult.handled;
              }
            }
          }
          return KeyEventResult.ignored;
        },
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Panel Kiri - Video Player (70% lebar)
              Expanded(
                flex: 7,
                child: VideoPlayerPanel(
                  player: _player,
                  controller: _controller,
                  currentVideoPath: _currentVideoPath,
                  pathController: _pathController,
                  onLoadVideo: _loadVideo,
                  onRecordScene: _recordScene,
                  onRecordOpening: _recordOpening,
                  onRecordClosing: _recordClosing,
                  autoSkipEnabled: _autoSkipEnabled,
                  onAutoSkipChanged: (val) {
                    setState(() => _autoSkipEnabled = val);
                  },
                  opStart: _opStart,
                  opEnd: _opEnd,
                  edStart: _edStart,
                  edEnd: _edEnd,
                ),
              ),
              const SizedBox(width: 16),
              
              // Panel Kanan - Catatan Adegan (30% lebar)
              Expanded(
                flex: 3,
                child: NotesPanel(
                  notes: _notes,
                  onDeleteNote: (id) {
                    setState(() {
                      _notes.removeWhere((n) => n.id == id);
                    });
                    _showSnackbar('Catatan dihapus', Colors.grey);
                  },
                  onEditNote: (id, newText) {
                    setState(() {
                      final idx = _notes.indexWhere((n) => n.id == id);
                      if (idx != -1) {
                        _notes[idx].note = newText;
                      }
                    });
                    _showSnackbar('Catatan disimpan', Colors.green);
                  },
                  onSeekTo: (duration) {
                    _player.seek(duration);
                  },
                  onAddManualNote: (text) {
                    if (_currentVideoPath.isEmpty) {
                      _showSnackbar('Buka video terlebih dahulu!', Colors.amber);
                      return;
                    }
                    final pos = _player.state.position;
                    setState(() {
                      _notes.add(SceneNote(
                        id: _uuid.v4(),
                        startTime: pos,
                        endTime: pos + const Duration(seconds: 5),
                        note: text,
                      ));
                    });
                    _showSnackbar('Catatan manual ditambahkan!', Colors.green);
                  },
                  onExportTxt: _exportToTxt,
                  onExportSrt: _exportToSrt,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
