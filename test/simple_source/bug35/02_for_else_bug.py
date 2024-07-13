# Adapted 3.5 from _bootstrap_external.py


def spec_from_file_location(loader, location):
    if loader:
        for _ in __file__:
            if location:
                break
        else:
            return None
