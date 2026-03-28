// Golden Path CI/CD Template — Jenkins Pipeline
// Standard pipeline for golden path compliance tracking.

pipeline {
    agent any

    environment {
        GOLDEN_PATH_TOKEN = credentials('golden-path-token')
        PYTHON_VERSION = '3.11'
    }

    stages {
        stage('Setup') {
            steps {
                sh 'python3 -m pip install -r requirements.txt'
            }
        }

        stage('Lint') {
            steps {
                sh 'flake8 --max-line-length=120 .'
            }
        }

        stage('Test') {
            steps {
                sh 'pytest tests/ -v --junitxml=test-results.xml'
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying via golden path pipeline'
            }
        }
    }

    post {
        always {
            echo "Pipeline complete: ${currentBuild.result}"
        }
    }
}
