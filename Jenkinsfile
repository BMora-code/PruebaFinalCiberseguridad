pipeline {
    agent any
    
    environment {
        APP_NAME = 'task-manager'
        DOCKER_IMAGE = "${APP_NAME}:${env.BUILD_ID}"
        ZAP_TARGET_URL = 'http://host.docker.internal:8080'
        ZAP_REPORT = 'zap_dast_report.json'
        BANDIT_DOCKER = 'docker.io/openlitespeed/bandit:latest'
        TRIVY_DOCKER = 'aquasec/trivy:latest'
        ZAP_DOCKER = 'owasp/zap2docker-stable'
    }

    stages {

        stage('Dependency & SAST') {
            steps {
                script {
                    echo "-> 1.1 Escaneo de Dependencias (Trivy FS)"
                    sh "docker run --rm -v \$(pwd):/data ${TRIVY_DOCKER} fs --format json --output trivy-deps.json /data"
                    sh "docker run --rm -v \$(pwd):/data ${TRIVY_DOCKER} fs --severity CRITICAL,HIGH --exit-code 1 /data"
                    archiveArtifacts artifacts: 'trivy-deps.json'

                    echo '-> 1.2 Análisis Estático con Bandit'
                    sh "docker run --rm -v \$(pwd):/app -w /app ${BANDIT_DOCKER} bandit -r . -f json -o bandit-report.json || true"
                    archiveArtifacts artifacts: 'bandit-report.json'
                }
            }
        }

        stage('Build & Image Scan') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE} ."

                echo '-> Escaneo de Imagen Docker'
                sh "docker run --rm -v \$(pwd):/root/.cache/ ${TRIVY_DOCKER} image --format json --output trivy-image.json ${DOCKER_IMAGE}"
                sh "docker run --rm -v \$(pwd):/root/.cache/ ${TRIVY_DOCKER} image --severity CRITICAL,HIGH --exit-code 1 ${DOCKER_IMAGE}"
                archiveArtifacts artifacts: 'trivy-image.json'
            }
        }

        stage('DAST with OWASP ZAP') {
            steps {
                script {
                    sh "docker run -d -p 8080:8080 --name ${APP_NAME}-staging ${DOCKER_IMAGE}"

                    sh """
                    docker run --rm -v \$(pwd):/zap/reports/ -i ${ZAP_DOCKER} \
                        zap-full-scan.py -t ${ZAP_TARGET_URL} \
                        -r /zap/reports/${ZAP_REPORT} -I || true
                    """

                    sh "docker stop ${APP_NAME}-staging && docker rm ${APP_NAME}-staging"

                    archiveArtifacts artifacts: "${ZAP_REPORT}"
                }
            }
        }

        stage('Deploy to Production') {
            steps {
                echo "-> Despliegue de la imagen ${DOCKER_IMAGE}"
                echo "Despliegue exitoso."
            }
        }
    }

    post {
        always {
            script {
                echo "--- Auditoría ---"
                echo "Build: ${env.BUILD_ID}, Commit: ${env.GIT_COMMIT}"
                echo "Artefactos archivados."
            }
        }
    }
}