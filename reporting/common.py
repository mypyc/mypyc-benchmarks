import os


def get_csv_path(data_repo: str, benchmark: str) -> str:
    data_dir = os.path.join(data_repo, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, benchmark + '.csv')
