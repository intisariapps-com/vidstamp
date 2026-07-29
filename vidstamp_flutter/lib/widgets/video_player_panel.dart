import 'dart:io';
import 'package:flutter/material.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

class VideoPlayerPanel extends StatefulWidget {
  final Player player;
  final VideoController controller;
  final String currentVideoPath;
  final TextEditingController pathController;
  final VoidCallback onLoadVideo;
  final VoidCallback onRecordScene;
  final VoidCallback onRecordOpening;
  final VoidCallback onRecordClosing;

  const VideoPlayerPanel({
    super.key,
    required this.player,
    required this.controller,
    required this.currentVideoPath,
    required this.pathController,
    required this.onLoadVideo,
    required this.onRecordScene,
    required this.onRecordOpening,
    required this.onRecordClosing,
  });

  @override
  State<VideoPlayerPanel> createState() => _VideoPlayerPanelState();
}

class _VideoPlayerPanelState extends State<VideoPlayerPanel> {
  bool _isPlaying = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  double _volume = 100.0;
  bool _isMuted = false;

  @override
  void initState() {
    super.initState();
    
    // Dengarkan status pemutaran
    widget.player.stream.playing.listen((playing) {
      if (mounted) setState(() => _isPlaying = playing);
    });

    widget.player.stream.position.listen((pos) {
      if (mounted) setState(() => _position = pos);
    });

    widget.player.stream.duration.listen((dur) {
      if (mounted) setState(() => _duration = dur);
    });

    widget.player.stream.volume.listen((vol) {
      if (mounted) setState(() => _volume = vol);
    });
  }

  String _formatTime(Duration duration) {
    final minutes = duration.inMinutes.toString().padLeft(2, '0');
    final seconds = (duration.inSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Input Path
        Container(
          padding: const EdgeInsets.only(bottom: 12),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: widget.pathController,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: 'Masukkan path absolut berkas video (.mkv / .mp4)...',
                    hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                    filled: true,
                    fillColor: const Color(0xFF16162A),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: Color(0xFF25254A)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: Colors.indigoAccent),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              ElevatedButton.icon(
                onPressed: widget.onLoadVideo,
                icon: const Icon(Icons.video_library_outlined, size: 18),
                label: const Text('Buka Video'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1A73E8),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ],
          ),
        ),

        // Video Screen Area
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              color: Colors.black,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF25254A), width: 1),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(11),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Video(
                    controller: widget.controller,
                    controls: null,
                  ),
                  
                  // Progress Slider dan Kontrol Overlay di bawah
                  Positioned(
                    bottom: 0,
                    left: 0,
                    right: 0,
                    child: Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.bottomCenter,
                          end: Alignment.topCenter,
                          colors: [Colors.black87, Colors.transparent],
                        ),
                      ),
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        children: [
                          // Slider waktu
                          Row(
                            children: [
                              Text(
                                _formatTime(_position),
                                style: const TextStyle(color: Colors.white, fontSize: 12),
                              ),
                              Expanded(
                                child: SliderTheme(
                                  data: SliderTheme.of(context).copyWith(
                                    trackHeight: 3.0,
                                    thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6.0),
                                    overlayShape: const RoundSliderOverlayShape(overlayRadius: 10.0),
                                    activeTrackColor: Colors.indigoAccent,
                                    inactiveTrackColor: Colors.grey.withOpacity(0.5),
                                    thumbColor: Colors.indigoAccent,
                                  ),
                                  child: Slider(
                                    value: _position.inMilliseconds.toDouble(),
                                    max: _duration.inMilliseconds.toDouble().clamp(1.0, double.infinity),
                                    onChanged: (val) {
                                      widget.player.seek(Duration(milliseconds: val.toInt()));
                                    },
                                  ),
                                ),
                              ),
                              Text(
                                _formatTime(_duration),
                                style: const TextStyle(color: Colors.white, fontSize: 12),
                              ),
                            ],
                          ),

                          // Tombol Kontrol Utama
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              // Playback Controls
                              Row(
                                children: [
                                  IconButton(
                                    icon: const Icon(Icons.replay_10, color: Colors.white),
                                    onPressed: () {
                                      widget.player.seek(_position - const Duration(seconds: 10));
                                    },
                                  ),
                                  IconButton(
                                    icon: Icon(
                                      _isPlaying ? Icons.pause_circle_filled : Icons.play_circle_filled,
                                      color: Colors.indigoAccent,
                                      size: 36,
                                    ),
                                    onPressed: () {
                                      widget.player.playOrPause();
                                    },
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.forward_10, color: Colors.white),
                                    onPressed: () {
                                      widget.player.seek(_position + const Duration(seconds: 10));
                                    },
                                  ),
                                ],
                              ),

                              // Volume & Mute
                              Row(
                                children: [
                                  IconButton(
                                    icon: Icon(
                                      _isMuted || _volume == 0.0
                                          ? Icons.volume_off
                                          : _volume < 50.0
                                              ? Icons.volume_down
                                              : Icons.volume_up,
                                      color: Colors.white,
                                    ),
                                    onPressed: () {
                                      setState(() {
                                        _isMuted = !_isMuted;
                                        widget.player.setVolume(_isMuted ? 0.0 : _volume);
                                      });
                                    },
                                  ),
                                  SizedBox(
                                    width: 80,
                                    child: SliderTheme(
                                      data: SliderTheme.of(context).copyWith(
                                        trackHeight: 2.0,
                                        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 4.0),
                                        activeTrackColor: Colors.white,
                                        inactiveTrackColor: Colors.white24,
                                        thumbColor: Colors.white,
                                      ),
                                      child: Slider(
                                        value: _volume,
                                        max: 100.0,
                                        onChanged: (val) {
                                          setState(() {
                                            _volume = val;
                                            _isMuted = false;
                                            widget.player.setVolume(_volume);
                                          });
                                        },
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),

        const SizedBox(height: 12),

        // Scene Recording Controls Panel
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF16162A),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFF25254A)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildRecorderButton(
                icon: Icons.fiber_manual_record,
                label: 'Catat Adegan',
                hotkey: 'Ctrl + R',
                color: Colors.redAccent,
                onPressed: widget.onRecordScene,
              ),
              _buildRecorderButton(
                icon: Icons.login,
                label: 'Set Opening',
                hotkey: 'Ctrl + O',
                color: Colors.amberAccent,
                onPressed: widget.onRecordOpening,
              ),
              _buildRecorderButton(
                icon: Icons.logout,
                label: 'Set Closing',
                hotkey: 'Ctrl + C',
                color: Colors.greenAccent,
                onPressed: widget.onRecordClosing,
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildRecorderButton({
    required IconData icon,
    required String label,
    required String hotkey,
    required Color color,
    required VoidCallback onPressed,
  }) {
    return InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Column(
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 18),
                const SizedBox(width: 8),
                Text(
                  label,
                  style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.black26,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                hotkey,
                style: const TextStyle(color: Colors.grey, fontSize: 10),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
