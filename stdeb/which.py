import os

# Implementation inspired by shutil.which from Python 3.3+
def which(program):
    def _is_executable(path):
        return os.path.isfile(path) and os.access(path, os.X_OK)

    path, _name = os.path.split(program)
    if path:
        if _is_executable(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if _is_executable(exe_file):
                return exe_file

    return None
