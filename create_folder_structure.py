import os

def print_folder_tree(start_path, indent=""):
    for item in sorted(os.listdir(start_path)):
        item_path = os.path.join(start_path, item)
        if os.path.isdir(item_path):
            print(indent + f"📁 {item}")
            print_folder_tree(item_path, indent + "    ")
        else:
            print(indent + f"📄 {item}")

if __name__ == "__main__":
    folder_path = r"C:\xampp\htdocs\Kenteh"
    
    if os.path.exists(folder_path):
        print(f"Folder tree for: {folder_path}\n")
        print_folder_tree(folder_path)
    else:
        print("The specified path does not exist.")
