class SceneNote {
  final String id;
  final Duration startTime;
  final Duration endTime;
  String note;

  SceneNote({
    required this.id,
    required this.startTime,
    required this.endTime,
    required this.note,
  });

  // Salin objek dengan beberapa field yang dimodifikasi
  SceneNote copyWith({
    String? id,
    Duration? startTime,
    Duration? endTime,
    String? note,
  }) {
    return SceneNote(
      id: id ?? this.id,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      note: note ?? this.note,
    );
  }

  // Format durasi menjadi string HH:MM:SS.mmm
  static String formatDuration(Duration duration) {
    final hours = duration.inHours.toString().padLeft(2, '0');
    final minutes = (duration.inMinutes % 60).toString().padLeft(2, '0');
    final seconds = (duration.inSeconds % 60).toString().padLeft(2, '0');
    final milliseconds = (duration.inMilliseconds % 1000).toString().padLeft(3, '0');
    return '$hours:$minutes:$seconds.$milliseconds';
  }
}
