import 'package:flutter/material.dart';
import '../models/scene_note.dart';

class NotesPanel extends StatefulWidget {
  final List<SceneNote> notes;
  final Function(String id) onDeleteNote;
  final Function(String id, String newNote) onEditNote;
  final Function(Duration start) onSeekTo;
  final Function(String text) onAddManualNote;
  final VoidCallback onExportTxt;
  final VoidCallback onExportSrt;

  const NotesPanel({
    super.key,
    required this.notes,
    required this.onDeleteNote,
    required this.onEditNote,
    required this.onSeekTo,
    required this.onAddManualNote,
    required this.onExportTxt,
    required this.onExportSrt,
  });

  @override
  State<NotesPanel> createState() => _NotesPanelState();
}

class _NotesPanelState extends State<NotesPanel> {
  final TextEditingController _noteInputController = TextEditingController();

  void _submitNote() {
    final text = _noteInputController.text.trim();
    if (text.isEmpty) return;
    widget.onAddManualNote(text);
    _noteInputController.clear();
  }

  @override
  void dispose() {
    _noteInputController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF111122),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF25254A)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header Panel
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              color: Color(0xFF16162A),
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(11),
                topRight: Radius.circular(11),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.note_alt_outlined, color: Colors.indigoAccent, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Catatan Adegan (${widget.notes.length})',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
                // Menu Ekspor
                PopupMenuButton<String>(
                  icon: const Icon(Icons.file_upload_outlined, color: Colors.white70, size: 20),
                  tooltip: 'Ekspor Catatan',
                  onSelected: (val) {
                    if (val == 'txt') {
                      widget.onExportTxt();
                    } else if (val == 'srt') {
                      widget.onExportSrt();
                    }
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'txt',
                      child: Row(
                        children: [
                          Icon(Icons.text_snippet_outlined, size: 18),
                          SizedBox(width: 8),
                          Text('Ekspor ke .txt'),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'srt',
                      child: Row(
                        children: [
                          Icon(Icons.subtitles_outlined, size: 18),
                          SizedBox(width: 8),
                          Text('Ekspor ke .srt'),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Daftar Catatan Adegan
          Expanded(
            child: widget.notes.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.notes, color: Colors.grey, size: 48),
                        SizedBox(height: 12),
                        Text(
                          'Belum ada adegan yang dicatat.\nGunakan hotkey Ctrl+R atau tombol di kiri.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey, fontSize: 12, height: 1.4),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    itemCount: widget.notes.length,
                    padding: const EdgeInsets.all(8),
                    itemBuilder: (context, index) {
                      final note = widget.notes[index];
                      return _buildNoteCard(note);
                    },
                  ),
          ),

          // Input Manual di Bawah
          Container(
            padding: const EdgeInsets.all(12),
            decoration: const BoxDecoration(
              color: Color(0xFF16162A),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(11),
                bottomRight: Radius.circular(11),
              ),
              border: Border(
                top: BorderSide(color: Color(0xFF25254A)),
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _noteInputController,
                    style: const TextStyle(color: Colors.white, fontSize: 13),
                    decoration: InputDecoration(
                      hintText: 'Tulis catatan manual di sini...',
                      hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                      filled: true,
                      fillColor: const Color(0xFF0D0D1A),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(6),
                        borderSide: const BorderSide(color: Color(0xFF25254A)),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(6),
                        borderSide: const BorderSide(color: Colors.indigoAccent),
                      ),
                    ),
                    onSubmitted: (_) => _submitNote(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send, color: Colors.indigoAccent, size: 20),
                  onPressed: _submitNote,
                  tooltip: 'Kirim Catatan',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNoteCard(SceneNote note) {
    final startStr = SceneNote.formatDuration(note.startTime);
    final endStr = SceneNote.formatDuration(note.endTime);

    return Card(
      color: const Color(0xFF1A1A32),
      margin: const EdgeInsets.symmetric(vertical: 4),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: Color(0xFF25254A)),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        title: InkWell(
          onTap: () => widget.onSeekTo(note.startTime),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Batasan Waktu (Timestamp Badge)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.indigo.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '$startStr --> $endStr',
                  style: const TextStyle(
                    color: Colors.indigoAccent,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'Courier',
                  ),
                ),
              ),
              const SizedBox(height: 6),
              // Teks Catatan
              Text(
                note.note,
                style: const TextStyle(color: Colors.white, fontSize: 13),
              ),
            ],
          ),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Edit Note
            IconButton(
              icon: const Icon(Icons.edit_outlined, color: Colors.grey, size: 18),
              onPressed: () => _showEditDialog(note),
              tooltip: 'Edit Catatan',
            ),
            // Delete Note
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 18),
              onPressed: () => widget.onDeleteNote(note.id),
              tooltip: 'Hapus Catatan',
            ),
          ],
        ),
      ),
    );
  }

  void _showEditDialog(SceneNote note) {
    final controller = TextEditingController(text: note.note);
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF16162A),
          title: const Text('Edit Catatan Adegan', style: TextStyle(color: Colors.white)),
          content: TextField(
            controller: controller,
            style: const TextStyle(color: Colors.white),
            decoration: const InputDecoration(
              enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.grey)),
              focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.indigoAccent)),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Batal', style: TextStyle(color: Colors.grey)),
            ),
            ElevatedButton(
              onPressed: () {
                widget.onEditNote(note.id, controller.text.trim());
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.indigoAccent),
              child: const Text('Simpan'),
            ),
          ],
        );
      },
    );
  }
}
