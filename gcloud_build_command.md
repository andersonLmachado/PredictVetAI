## Google Cloud Build Command

To build your Docker image and push it to Google Container Registry (GCR) or Artifact Registry, use the following command:

```bash
gcloud builds submit --tag gcr.io/{SEU_ID_DO_PROJETO_GCP}/{NOME_DA_SUA_IMAGEM}:latest .
```

### Explanation:

*   `gcloud builds submit`: This is the primary Google Cloud SDK command used to submit your source code and Dockerfile to Google Cloud Build. Cloud Build will then execute the build process as defined in your Dockerfile (or a build config file if specified).

*   `--tag gcr.io/{SEU_ID_DO_PROJETO_GCP}/{NOME_DA_SUA_IMAGEM}:latest`: This flag specifies the name and tag for the Docker image that will be built.
    *   `gcr.io`: This prefix indicates that the Docker image will be stored in Google Container Registry.
    *   `{SEU_ID_DO_PROJETO_GCP}`: This is a placeholder for your unique Google Cloud Project ID. You need to replace this with your actual project ID.
    *   `{NOME_DA_SUA_IMAGEM}`: This is a placeholder for the name you want to give your Docker image (e.g., `my-python-app`, `adk-server`).
    *   `:latest`: This is the tag applied to this specific build of the image. `latest` is a common convention for the most recent version. You can use other tags like `v1.0`, `dev`, `staging`, etc., to manage different versions of your image.

*   `.` (a period): This argument specifies the build context. The build context is the set of files that Google Cloud Build will have access to during the build process. A `.` means that the current directory (where you run the command) and its subdirectories will be sent to Cloud Build. Your Dockerfile should be in the root of this context.

### Note on Artifact Registry:

If you prefer to use **Artifact Registry** instead of Google Container Registry, you need to modify the image tag format. Artifact Registry provides more advanced features for managing artifacts, including regional repositories.

The command would look like this:

```bash
gcloud builds submit --tag REGION-docker.pkg.dev/{SEU_ID_DO_PROJETO_GCP}/{NOME_DO_REPOSITORIO}/{NOME_DA_SUA_IMAGEM}:latest .
```

**Key differences for Artifact Registry:**

*   Replace `gcr.io` with `REGION-docker.pkg.dev`.
    *   `REGION`: The Google Cloud region where your Artifact Registry repository is located (e.g., `us-central1`, `europe-west1`).
*   `{SEU_ID_DO_PROJETO_GCP}`: Your Google Cloud Project ID.
*   `{NOME_DO_REPOSITORIO}`: The name of the Docker repository you created in Artifact Registry. You must create this repository in Artifact Registry before you can push images to it.
*   `{NOME_DA_SUA_IMAGEM}`: The name for your Docker image.
*   `:latest`: The image tag.

Ensure you have an Artifact Registry Docker repository created in the specified region and project before running this command. You may also need to grant appropriate permissions to the Cloud Build service account to push to Artifact Registry.
