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
PROJECT_NAME= <your gee project name>
DRIVE_FOLDER_ID= <your drive folder id>
DRIVE_FOLDER_NAME= <your drive folder name>
IMAGE_COLLECTION_PATH= <your local image collection folder path>
QUALITY_FILE_PATH= <your local qualtiy recording file path>
TRACKER_FOLDER_PATH= <your local tracker folder path>
CREDENTIALS_FILE_PATH= <your drive OAuth2.0 credientail file path>
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