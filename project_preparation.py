
import os


def main():

    cwd = os.getcwd()
    electron_path = cwd + "\\electron-quick-start"

    os.system("git clone https://github.com/electron/electron-quick-start")
    os.chdir(electron_path)
    os.system("npm install")
    if os.path.isfile("index.html"):
        os.remove("index.html")
    else:
        print("Error: %s file not found" % "index.html")

if __name__ == "__main__":
    main()