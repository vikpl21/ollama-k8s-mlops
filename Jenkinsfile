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
                dir('app') {
                    sh '''
                        python3 -m pip install --user --break-system-packages --quiet ruff
                        python3 -m ruff check .
                    '''
                }
            }
        }

        stage('Test (pytest)') {
            steps {
                dir('app') {
                    sh '''
                        python3 -m pip install --user --break-system-packages --quiet -r requirements.txt
                        python3 -m pip install --user --break-system-packages --quiet pytest
                        python3 -m pytest -v tests/
                    '''
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG -f app/Dockerfile app'
            }
        }

        stage('Validate K8s manifests (kubeconform)') {
            steps {
                sh '''
                    curl -sSL https://github.com/yannh/kubeconform/releases/latest/download/kubeconform-linux-amd64.tar.gz | tar xz -C /tmp kubeconform
                    /tmp/kubeconform -summary -ignore-missing-schemas k8s
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
