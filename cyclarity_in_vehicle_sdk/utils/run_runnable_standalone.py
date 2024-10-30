from typing import Optional
import shlex
from contextlib import contextmanager
import importlib
import inspect
import sys
import zipfile
import jsonargparse

def start(runnable_zip_path: str, cli_args: str, package_name: str, class_name: str):

    _extract_zip(runnable_zip_path)
    with _dynamic_import(package_name, class_name) as runnable_class:
        run_from_cli(runnable=runnable_class, cli_args=cli_args)

def _extract_zip(file):
    with zipfile.ZipFile(file) as z:
        z.extractall(path="/tmp/runnable/")  

@contextmanager
def _dynamic_import(module_name, entrypoint_runnable_class):
    is_found = False
    try:
        print(f"importing step - entrypoint file: {module_name}, class:{entrypoint_runnable_class}")
        sys.path.insert(0, '/tmp/runnable') if '/tmp/runnable' not in sys.path else None
        module = importlib.import_module(module_name)
        from cyclarity_sdk.expert_builder import Runnable

        classes = inspect.getmembers(module, inspect.isclass)
        for class_ in classes:
            class_name = class_[0]
            class_attr = class_[1]
            print(f'entrypoint_runnable_class {entrypoint_runnable_class}')
            print (f'class_name {class_name}' )
            print (f'class_attr {class_attr}' )

            if issubclass(class_attr, Runnable) and class_attr != Runnable and class_name == entrypoint_runnable_class:
                print(f"Class - {class_name}, successfully imported")
                is_found = True
                yield class_attr
        if not is_found:
            raise ImportError(
                f"Class {entrypoint_runnable_class} from type Runnable wasn't found in {module_name}\nAvailable class - {classes}")
    except ImportError as e:
        print(f"Runnable file not found - {e}")
    except AttributeError as e:
        print(f"Function not found - {e}")
    
    del sys.modules[module_name]
    del module

def run_from_cli(runnable, cli_args: Optional[str] = None):
    parser = jsonargparse.ArgumentParser()
    parser.add_argument("--config", action="config")
    parser.add_class_arguments(runnable)

    if isinstance(cli_args, str):
        args_list = shlex.split(cli_args)  
    else:
        args_list=cli_args

    args = parser.parse_args(args_list)
    instances = parser.instantiate_classes(args)

    runner = runnable(**instances)
    with runner:
        results = runner()   
        print(results.description)

def main():

    parser = jsonargparse.ArgumentParser(description='Standalone Runnable package execution')
    parser.add_argument('--runnable_zip_path', action="store", dest='runnable_zip_path', default="./runnable.zip")
    parser.add_argument('--cli_args', action="store", dest='cli_args')
    parser.add_argument('--package_name', action="store", dest='package_name')
    parser.add_argument('--class_name', action="store", dest='class_name')
    args = parser.parse_args()


    start(runnable_zip_path=args.runnable_zip_path, cli_args=args.cli_args, package_name=args.package_name, class_name=args.class_name)

if __name__ == "__main__":
    main()
