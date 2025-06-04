## Google Cloud Run Deploy Command

To deploy your Docker container image to Google Cloud Run, use the following command:

```bash
gcloud run deploy {NOME_DO_SERVICO} \
  --image gcr.io/{SEU_ID_DO_PROJETO_GCP}/{NOME_DA_SUA_IMAGEM}:latest \
  --platform managed \
  --region {REGIAO_GCP} \
  --set-env-vars GOOGLE_API_KEY="{SUA_CHAVE_API_GEMINI}" \
  --timeout 900s \
  --allow-unauthenticated
```

### Explanation:

*   `gcloud run deploy {NOME_DO_SERVICO}`: This is the Google Cloud SDK command used to deploy a container image to Cloud Run. If a service with the name `{NOME_DO_SERVICO}` doesn't exist, this command will create it. If it already exists, this command will create a new revision of that service with the updated configuration.
    *   `{NOME_DO_SERVICO}`: This is a placeholder for the name you want to give your Cloud Run service (e.g., `my-llm-api`, `adk-service`). Choose a name that is unique within your project and region.

*   `--image gcr.io/{SEU_ID_DO_PROJETO_GCP}/{NOME_DA_SUA_IMAGEM}:latest`: This flag specifies the Docker container image to be deployed.
    *   This path should exactly match the image you built and pushed using `gcloud builds submit` (or other methods).
    *   `gcr.io/{SEU_ID_DO_PROJETO_GCP}/{NOME_DA_SUA_IMAGEM}:latest`: This format is for images stored in Google Container Registry.
        *   `{SEU_ID_DO_PROJETO_GCP}`: Your Google Cloud Project ID.
        *   `{NOME_DA_SUA_IMAGEM}`: The name of your Docker image.
        *   `:latest`: The tag of the image you want to deploy.
    *   **If you used Artifact Registry:** The image path needs to be updated to `REGION-docker.pkg.dev/{SEU_ID_DO_PROJETO_GCP}/{NOME_DO_REPOSITORIO}/{NOME_DA_SUA_IMAGEM}:latest`.
        *   `REGION`: The Google Cloud region of your Artifact Registry repository.
        *   `{NOME_DO_REPOSITORIO}`: The name of your repository in Artifact Registry.

*   `--platform managed`: This flag specifies that you are deploying to the fully managed Cloud Run platform. This means Google handles the underlying infrastructure, scaling, etc. The alternative is `--platform gke` for Cloud Run for Anthos, which runs on a Google Kubernetes Engine cluster.

*   `--region {REGIAO_GCP}`: This placeholder indicates the Google Cloud region where your service will be deployed and run (e.g., `us-central1`, `europe-west1`, `asia-east1`). Choose a region that is close to your users or other services it interacts with.

*   `--set-env-vars GOOGLE_API_KEY="{SUA_CHAVE_API_GEMINI}"`: This flag allows you to set environment variables that will be available to your application running inside the Cloud Run service.
    *   `GOOGLE_API_KEY="{SUA_CHAVE_API_GEMINI}"`: This specifically sets an environment variable named `GOOGLE_API_KEY`. Your application code (e.g., `agent.py`) can then access this key to authenticate with Google AI services like the Gemini API.
        *   `{SUA_CHAVE_API_GEMINI}`: **Crucially, you must replace this placeholder with your actual Gemini API key.**

*   `--timeout 900s`: This flag sets the maximum time Cloud Run will wait for a request to be processed by your service before it's considered to have timed out. It's set to `900s` (900 seconds, or 15 minutes). This can be important for applications involving Large Language Models (LLMs), as generating responses can sometimes take longer than default timeouts. The maximum timeout allowed by Cloud Run is 3600 seconds (60 minutes).

*   `--allow-unauthenticated`: This flag makes your deployed service publicly accessible over the internet. Anyone with the URL will be able to send requests to it.
    *   This is suitable for public APIs or web applications.
    *   If your service should be private and only accessible by specific users or other services within your Google Cloud environment, you should **omit** this flag. You would then configure Identity and Access Management (IAM) to control access.

### Important Note on Placeholders:

Remember to replace all placeholders enclosed in curly braces `{}` with your actual values before running the command. For example:
*   `{NOME_DO_SERVICO}`
*   `{SEU_ID_DO_PROJETO_GCP}`
*   `{NOME_DA_SUA_IMAGEM}`
*   `{REGIAO_GCP}`
*   `{SUA_CHAVE_API_GEMINI}`
*   And if using Artifact Registry, also `{NOME_DO_REPOSITORIO}` and `REGION` in the image path.
