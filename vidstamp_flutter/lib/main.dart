import 'package:flutter/material.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';
import 'dart:io';

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
      title: 'VidStamp Flutter Prototype',
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.indigo,
        scaffoldBackgroundColor: const Color(0xFF0D0D1A),
      ),
      home: const VideoPlayerScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class VideoPlayerScreen extends StatefulWidget {
  const VideoPlayerScreen({super.key});

  @override
  State<VideoPlayerScreen> createState() => _VideoPlayerScreenState();
}

class _VideoPlayerScreenState extends State<VideoPlayerScreen> {
  late final Player player;
  late final VideoController controller;
  final TextEditingController _pathController = TextEditingController();
  
  bool _isPlaying = false;
  String _currentVideo = "";

  @override
  void initState() {
    super.initState();
    // Inisialisasi player & controller
    player = Player();
    controller = VideoController(player);

    // Dengar status pemutaran
    player.stream.playing.listen((playing) {
      if (mounted) {
        setState(() {
          _isPlaying = playing;
        });
      }
    });

    // Default path (mengambil argumen dari script uji coba mpv jika ada)
    _pathController.text = r"E:\ANIME\[Kusonime] Ragna Crimson 01-12 1080p\[Kusonime] Ragna Crimson 01-12 1080p\[Kusonime] Ragna Crimson - 01.mkv";
  }

  @override
  void dispose() {
    player.dispose();
    _pathController.dispose();
    super.dispose();
  }

  void _loadVideo() {
    final path = _pathController.text.trim();
    if (path.isEmpty) return;

    final file = File(path);
    if (file.existsSync()) {
      setState(() {
        _currentVideo = path;
      });
      player.open(Media(file.path));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('File tidak ditemukan: $path'),
          backgroundColor: Colors.redAccent,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🎬 VidStamp Flutter - media_kit Prototype'),
        backgroundColor: const Color(0xFF16213E),
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Baris Input Path Video
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _pathController,
                    decoration: const InputDecoration(
                      labelText: 'Path Video Lokal (.mkv / .mp4)',
                      border: OutlineInputBorder(),
                      hintText: 'Masukkan path absolut ke file video...',
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: _loadVideo,
                  icon: const Icon(Icons.video_library),
                  label: const Text('Muat Video'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0F3460),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            
            // Area Pemutar Video
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF1A1A2E), width: 2),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: Center(
                    child: Video(
                      controller: controller,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // Informasi Video & Kontrol Sederhana
            if (_currentVideo.isNotEmpty)
              Text(
                'Memutar: ${File(_currentVideo).path}',
                style: const TextStyle(color: Colors.grey, fontSize: 12),
                overflow: TextOverflow.ellipsis,
              ),
            const SizedBox(height: 8),
            
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.replay_10),
                  onPressed: () {
                    player.seek(player.state.position - const Duration(seconds: 10));
                  },
                  iconSize: 32,
                  color: Colors.white,
                ),
                const SizedBox(width: 20),
                FloatingActionButton(
                  onPressed: () {
                    player.playOrPause();
                  },
                  backgroundColor: const Color(0xFFE94560),
                  child: Icon(
                    _isPlaying ? Icons.pause : Icons.play_arrow,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 20),
                IconButton(
                  icon: const Icon(Icons.forward_10),
                  onPressed: () {
                    player.seek(player.state.position + const Duration(seconds: 10));
                  },
                  iconSize: 32,
                  color: Colors.white,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
