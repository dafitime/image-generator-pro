"""
src/logic/history.py
Manages Undo/Redo stacks for the application.
"""
class Command:
    """Base class for an action."""
    def undo(self): pass
    def redo(self): pass

class UpdateMetadataCommand(Command):
    def __init__(self, model_list, file_id, old_data, new_data, update_ui_callback):
        self.model_list = model_list  # The list inside current_plan
        self.file_id = file_id        # path to identify file
        self.old_data = old_data      # dict copy
        self.new_data = new_data      # dict copy
        self.callback = update_ui_callback

    def undo(self):
        # Revert data
        target = next((f for f in self.model_list if f['original_path'] == self.file_id), None)
        if target:
            target.update(self.old_data)
            self.callback(self.file_id)

    def redo(self):
        # Apply new data
        target = next((f for f in self.model_list if f['original_path'] == self.file_id), None)
        if target:
            target.update(self.new_data)
            self.callback(self.file_id)

class HistoryManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def push(self, command):
        self.undo_stack.append(command)
        self.redo_stack.clear() # New action clears redo history

    def undo(self):
        if not self.undo_stack: return
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)
        return "Undo Performed"

    def redo(self):
        if not self.redo_stack: return
        cmd = self.redo_stack.pop()
        cmd.redo()
        self.undo_stack.append(cmd)
        return "Redo Performed"