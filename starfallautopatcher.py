import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class StarfallPatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Starfall EX Effect Patcher")
        self.root.geometry("650x480")
        self.root.minsize(500, 350)
        
        self.selected_folder = ""
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.create_widgets()
        
    def create_widgets(self):
        top_frame = ttk.LabelFrame(self.root, text="Target Directory", padding="10")
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.folder_label = ttk.Label(top_frame, text="No folder selected", wraplength=450, foreground="gray")
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.select_btn = ttk.Button(top_frame, text="Browse Folder", command=self.browse_folder)
        self.select_btn.pack(side=tk.RIGHT)
        
        options_frame = ttk.LabelFrame(self.root, text="Options", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.txt_var = tk.BooleanVar(value=True)
        self.lua_var = tk.BooleanVar(value=True)
        
        txt_chk = ttk.Checkbutton(options_frame, text="Patch .txt files", variable=self.txt_var)
        txt_chk.pack(side=tk.LEFT, padx=15)
        
        lua_chk = ttk.Checkbutton(options_frame, text="Patch .lua files", variable=self.lua_var)
        lua_chk.pack(side=tk.LEFT, padx=15)
        
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_label = ttk.Label(log_frame, text="Log Output:")
        log_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=12, font=("Consolas", 10))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(bottom_frame, text="Select your Starfall scripts folder to begin.")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.clear_btn = ttk.Button(bottom_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        self.start_btn = ttk.Button(bottom_frame, text="Start Patching", command=self.start_patching_thread, state=tk.DISABLED)
        self.start_btn.pack(side=tk.RIGHT)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder containing Starfall Scripts")
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=folder, foreground="black")
            self.start_btn.config(state=tk.NORMAL)
            self.status_label.config(text="Ready to patch. Click 'Start Patching'.")
            self.log(f"Selected: {folder}")
            
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        
    def clear_log(self):
        self.log_text.delete("1.0", tk.END)
        
    def start_patching_thread(self):
        self.start_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Scanning and patching files...")
        
        thread = threading.Thread(target=self.patch_files)
        thread.daemon = True
        thread.start()
        
    def patch_files(self):
        exts = []
        if self.txt_var.get():
            exts.append(".txt")
        if self.lua_var.get():
            exts.append(".lua")
            
        if not exts:
            self.root.after(0, lambda: messagebox.showwarning("Warning", "Please select at least one file extension."))
            self.root.after(0, self.reset_ui)
            return
            
        files_to_patch = []
        for root_dir, _, filenames in os.walk(self.selected_folder):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in exts:
                    files_to_patch.append(os.path.join(root_dir, filename))
                    
        if not files_to_patch:
            self.root.after(0, lambda: self.log("No matching files found."))
            self.root.after(0, lambda: self.status_label.config(text="Finished. No files found."))
            self.root.after(0, self.reset_ui)
            return
            
        self.log(f"Found {len(files_to_patch)} file(s) to scan.\n")
        
        patched_count = 0
        scanned_count = 0
        
        for file_path in files_to_patch:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                new_content, changes_made = self.perform_patch(content)
                
                scanned_count += 1
                if changes_made > 0:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    patched_count += 1
                    rel_path = os.path.relpath(file_path, self.selected_folder)
                    self.log(f"Patched: {rel_path} -> ({changes_made} effect(s) converted)")
                    
            except Exception as e:
                self.log(f"Failed to process {file_path}: {str(e)}")
                
        self.log(f"\n--- Done ---")
        self.log(f"Scanned: {scanned_count} files")
        self.log(f"Patched: {patched_count} files")
        
        self.root.after(0, lambda: self.status_label.config(text=f"Completed. Patched {patched_count} file(s)."))
        self.root.after(0, lambda: messagebox.showinfo("Finished", f"Successfully patched {patched_count} of {scanned_count} files!"))
        self.root.after(0, self.reset_ui)
        
    def reset_ui(self):
        self.start_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.NORMAL)

    def perform_patch(self, content):
        SETTER_MAP = {
            "angles": "angles",
            "attachment": "attachment",
            "color": "color",
            "damagetype": "damagetype",
            "entindex": "entindex",
            "entity": "entity",
            "flags": "flags",
            "hitbox": "hitbox",
            "magnitude": "magnitude",
            "materialindex": "materialindex",
            "normal": "normal",
            "origin": "origin",
            "radius": "radius",
            "scale": "scale",
            "start": "start",
            "surfaceprop": "surfaceprop"
        }

        def find_matching_paren(text, open_idx):
            count = 1
            for i in range(open_idx + 1, len(text)):
                if text[i] == '(':
                    count += 1
                elif text[i] == ')':
                    count -= 1
                    if count == 0:
                        return i
            return -1

        def expand_to_full_line_if_alone(text, start, end):
            line_start = text.rfind('\n', 0, start) + 1
            line_end = text.find('\n', end)
            if line_end == -1:
                line_end = len(text)
                
            before = text[line_start:start]
            after = text[end:line_end]
            
            if before.strip() == '' and (after.strip() == '' or after.strip() == ';'):
                if line_end < len(text) and text[line_end] == '\n':
                    return line_start, line_end + 1
                return line_start, line_end
            else:
                trailing = re.match(r'[ \t]*;?[ \t]*', text[end:])
                if trailing:
                    end += trailing.end()
                return start, end

        edits = []
        processed_spans = set()
        
        chain_pattern = re.compile(r'effect\.create\s*\(')
        for chain_match in chain_pattern.finditer(content):
            c_start = chain_match.start()
            if any(s <= c_start < e for s, e, _ in edits):
                continue
                
            line_start = content.rfind('\n', 0, c_start) + 1
            pre_text = content[line_start:c_start]
            assign_match = re.search(r'(?:local\s+)?(\b\w+\b)\s*=\s*$', pre_text)
            
            if not assign_match:
                c_open = chain_match.end() - 1
                c_close = find_matching_paren(content, c_open)
                if c_close == -1:
                    continue
                    
                initial_arg = content[c_open + 1 : c_close].strip()
                curr_pos = c_close + 1
                
                chain_props = {}
                effect_name = initial_arg
                chain_end = curr_pos
                is_chain = False
                
                while True:
                    method_match = re.match(r'[ \t\n]*:([a-zA-Z0-9_]+)\s*\(', content[curr_pos:])
                    if not method_match:
                        break
                    
                    method_name = method_match.group(1)
                    m_open = curr_pos + method_match.end() - 1
                    m_close = find_matching_paren(content, m_open)
                    if m_close == -1:
                        break
                        
                    m_arg = content[m_open + 1 : m_close].strip()
                    curr_pos = m_close + 1
                    chain_end = curr_pos
                    is_chain = True
                    
                    m_lower = method_name.lower()
                    if m_lower.startswith("set") and m_lower[3:] in SETTER_MAP:
                        key = SETTER_MAP[m_lower[3:]]
                        chain_props[key] = m_arg
                    elif m_lower == "play":
                        if m_arg:
                            effect_name = m_arg
                            
                if is_chain and effect_name:
                    if chain_props:
                        prop_str = ", ".join(f"{k} = {v}" for k, v in chain_props.items())
                        replacement = f"effect.create({effect_name}, {{ {prop_str} }})"
                    else:
                        replacement = f"effect.create({effect_name}, {{}})"
                    edits.append((c_start, chain_end, replacement))

        create_pattern = re.compile(r'(?:local\s+)?(\b\w+\b)\s*=\s*effect\.create\s*\(')
        for create_match in create_pattern.finditer(content):
            decl_start = create_match.start()
            if any(s <= decl_start < e for s, e, _ in edits):
                continue
                
            var_name = create_match.group(1)
            open_paren = create_match.end() - 1
            close_paren = find_matching_paren(content, open_paren)
            if close_paren == -1:
                continue
                
            init_arg = content[open_paren + 1 : close_paren].strip()
            decl_end = close_paren + 1
            
            search_start = decl_end
            play_pattern = re.compile(rf'\b{re.escape(var_name)}:play\s*\(')
            play_match = play_pattern.search(content, search_start)
            if not play_match:
                continue
                
            play_open = play_match.end() - 1
            play_close = find_matching_paren(content, play_open)
            if play_close == -1:
                continue
                
            play_arg = content[play_open + 1 : play_close].strip()
            effect_name = play_arg if play_arg else init_arg
            if not effect_name:
                continue
                
            search_region = content[decl_end : play_match.start()]
            setter_pattern = re.compile(rf'\b{re.escape(var_name)}:([a-zA-Z0-9_]+)\s*\(')
            
            properties = {}
            setter_spans = []
            
            for s_match in setter_pattern.finditer(search_region):
                method_name = s_match.group(1)
                m_open = decl_end + s_match.end() - 1
                m_close = find_matching_paren(content, m_open)
                if m_close == -1:
                    continue
                    
                arg_val = content[m_open + 1 : m_close].strip()
                m_lower = method_name.lower()
                if m_lower.startswith("set") and m_lower[3:] in SETTER_MAP:
                    key = SETTER_MAP[m_lower[3:]]
                    properties[key] = arg_val
                    setter_spans.append((decl_end + s_match.start(), m_close + 1))
                    
            play_line_start = content.rfind('\n', 0, play_match.start()) + 1
            play_indent = re.match(r'^[ \t]*', content[play_line_start : play_match.start()]).group(0)
            
            if len(properties) >= 2:
                prop_indent = play_indent + "    "
                table_body = ",\n".join(f"{prop_indent}{k} = {v}" for k, v in properties.items())
                replacement = f"effect.create({effect_name}, {{\n{table_body}\n{play_indent}}})"
            elif len(properties) == 1:
                prop_str = ", ".join(f"{k} = {v}" for k, v in properties.items())
                replacement = f"effect.create({effect_name}, {{ {prop_str} }})"
            else:
                replacement = f"effect.create({effect_name}, {{}})"
                
            edits.append((play_match.start(), play_close + 1, replacement))
            
            d_s, d_e = expand_to_full_line_if_alone(content, decl_start, decl_end)
            edits.append((d_s, d_e, ""))
            
            for s_start, s_end in setter_spans:
                exp_s, exp_e = expand_to_full_line_if_alone(content, s_start, s_end)
                edits.append((exp_s, exp_e, ""))

        if not edits:
            return content, 0
            
        unique_edits = {}
        for s, e, r in edits:
            if s not in unique_edits or len(r) > len(unique_edits[s][1]):
                unique_edits[s] = (e, r)
                
        sorted_edits = sorted([(s, e, r) for s, (e, r) in unique_edits.items()], key=lambda x: x[0], reverse=True)
        
        new_content = list(content)
        count = 0
        for s, e, r in sorted_edits:
            new_content[s:e] = list(r)
            if r.startswith("effect.create"):
                count += 1
                
        return "".join(new_content), count

if __name__ == "__main__":
    root = tk.Tk()
    app = StarfallPatcherApp(root)
    root.mainloop()