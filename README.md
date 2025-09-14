# LST_series

Calculation land surface temperature using Landsat and MODIS series.

## Usage

### Environment setup

Install python environment using conda:

```bash
conda create -f environment.yml
conda activate gee
```

Create a `.env`  file in the root directory and add the following variables:

```bash
cp .env.example .env
```

```bash # .env
IMAGE_COLLECTION_PATH=your local path to save images (required)
QUALITY_FILE_PATH=your local path to save record file (required)
MONITOR_FOLDER_PATH=your local path to save monitor info (required)
DRIVE_FOLDER_ID=google drive folder id (required)
PROJECT_NAME=your own gee project (required)
```

### Google authentication

1. run `gee_auth_script.ipynb`;
2. Download google oauth2.0 file and name it `client_secret.json`, put it in the root directory;
3. Create a `settings.yaml` file in the root directory;

```bash
cp settings.yaml.example settings.yaml
```

### Export LST image to Google Drive and Download

First run test script to check if the environment is set up correctly:

```bash
python tests/test.py
```

If the script runs successfully, you can run the main script:

```bash
python -m src
```