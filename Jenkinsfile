pipeline {
    agent any

    environment {
        IMAGE_NAME = 'ollama-k8s-mlops-fastapi'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/vikpl21/ollama-k8s-mlops.git',
                    credentialsId: 'github-vikpl21'
            }
        }

        stage('Lint (ruff)') {
            steps {
                sh '''
                    docker run --rm -v "$PWD":/app -w /app python:3.11-slim \
                      sh -c "pip install --quiet ruff && ruff check ."
                '''
            }
        }

        stage('Test (pytest)') {
            steps {
                sh '''
                    docker run --rm -v "$PWD":/app -w /app python:3.11-slim \
                      sh -c "pip install --quiet -r requirements.txt && pytest -v"
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG .'
            }
        }

        stage('Validate K8s manifests (kubeconform)') {
            steps {
                sh '''
                    docker run --rm -v "$PWD":/data ghcr.io/yannh/kubeconform:latest \
                      -summary /data/k8s/*.yaml
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline zakończony sukcesem — zbudowano obraz ${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo "Pipeline nie powiódł się — sprawdź logi powyższych etapów."
        }
    }
}
