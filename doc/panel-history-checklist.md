
# Implementation Checklist

## Phase 1: Setup (30min)
- [ ] Create branch `feature/panel-history`
- [ ] Add `PanelHistory` model to config.py
- [ ] Add `_marked_dirs` to F2Commander.__init__()

## Phase 2: Core Logic (1.5h)
- [ ] Implement `_mark_directory_as_used()`
- [ ] Add `NavigatedToDir` message to filelist.py
- [ ] Hook in `on_file_selected()`
- [ ] Hook in `on_navigated_to_dir()`

## Phase 3: User Commands (1h)
- [ ] Add Ctrl+1-4 bindings
- [ ] Implement `_jump_to_history_slot()`
- [ ] Handle invalid URLs gracefully

## Phase 4: Testing (1h)
- [ ] Test cursor movement tracking
- [ ] Test operations (edit, view, copy, etc.)
- [ ] Test navigation (Enter, backspace, Ctrl+G)
- [ ] Test panel swap scenario
- [ ] Test remote filesystem edge cases
- [ ] Test config persistence

## Phase 5: Documentation (30min)
- [ ] Update README.md with feature description
- [ ] Add example config snippet
- [ ] Document hotkeys in help
