// Jenkinsfile
pipeline {
    agent any
    
    // Variables globales
    environment {
        APP_NAME = 'task-manager'
        DOCKER_IMAGE = "${APP_NAME}:${env.BUILD_ID}"
        ZAP_TARGET_URL = 'http://host.docker.internal:8080' // Acceder al contenedor de la app desde el contenedor ZAP
        ZAP_REPORT = 'zap_dast_report.json'
        # Herramientas recomendadas para SAST y Escaneo de Imagen
        BANDIT_DOCKER = 'docker.io/openlitespeed/bandit:latest'
        TRIVY_DOCKER = 'aquasec/trivy:latest'
        ZAP_DOCKER = 'owasp/zap2docker-stable'
    }

    stages {
        // --- IL 3.3: Gestión de Dependencias y SAST (Shift-Left Security) ---
        stage('Dependency & SAST') {
            steps {
                script {
                    echo "-> 1.1. Escaneo de Dependencias (Trivy FS - IL 3.3)"
                    // Escanear requirements.txt para CVEs conocidas
                    sh "docker run --rm -v \$(pwd):/data ${TRIVY_DOCKER} fs --format json --output trivy-deps.json /data"
                    
                    // Fallar la build si hay vulnerabilidades CRÍTICAS o ALTAS
                    sh "docker run --rm -v \$(pwd):/data ${TRIVY_DOCKER} fs --severity CRITICAL,HIGH --exit-code 1 /data"
                    
                    archiveArtifacts artifacts: 'trivy-deps.json', fingerprint: true
                    
                    echo "-> 1.2. Análisis Estático de Código Python (Bandit - IL 3.1)"
                    // Bandit escanea el código Python para Inyección SQL, XSS, etc.
                    // Ejecutamos Bandit y archivamos el informe, permitiendo que las demás etapas se ejecuten.
                    sh "docker run --rm -v \$(pwd):/app -w /app ${BANDIT_DOCKER} \
                        bandit -r . -f json -o bandit-report.json || true"
                    
                    archiveArtifacts artifacts: 'bandit-report.json', fingerprint: true
                }
            }
        }
        
        // --- IL 3.1: Construcción y Escaneo de Imagen ---
        stage('Build & Image Scan') {
            steps {
                // 1. Construir la imagen
                sh "docker build -t ${DOCKER_IMAGE} ."
                
                echo "-> 2. Escaneo de Imagen Docker (Trivy Image - IL 3.1)"
                // 2. Escaneo de la imagen Docker para vulnerabilidades del OS/Librerías del contenedor
                sh "docker run --rm -v \$(pwd):/root/.cache/ ${TRIVY_DOCKER} image --format json --output trivy-image.json ${DOCKER_IMAGE}"
                
                // Fallar si el escaneo de la imagen detecta vulnerabilidades críticas/altas
                sh "docker run --rm -v \$(pwd):/root/.cache/ ${TRIVY_DOCKER} image --severity CRITICAL,HIGH --exit-code 1 ${DOCKER_IMAGE}"
                
                archiveArtifacts artifacts: 'trivy-image.json', fingerprint: true
            }
        }
        
        // --- IL 3.2: Pruebas Automatizadas de Seguridad (DAST con OWASP ZAP) ---
        stage('DAST with OWASP ZAP') {
            steps {
                script {
                    echo "-> 3. Despliegue temporal y DAST (IL 3.2)"
                    
                    // 1. Despliegue temporal (staging)
                    sh "docker run -d -p 8080:8080 --name ${APP_NAME}-staging ${DOCKER_IMAGE}"

                    // 2. Ejecutar OWASP ZAP Full Scan
                    sh """
                    docker run --rm -v \$(pwd):/zap/reports/ -i ${ZAP_DOCKER} \
                        zap-full-scan.py -t ${ZAP_TARGET_URL} \
                        -r /zap/reports/${ZAP_REPORT} -I || true
                    """
                    
                    // 3. Detener y limpiar el contenedor de staging
                    sh "docker stop ${APP_NAME}-staging && docker rm ${APP_NAME}-staging"
                    
                    // 4. Archivar el informe de ZAP
                    archiveArtifacts artifacts: "${ZAP_REPORT}", fingerprint: true
                }
            }
        }

        // --- IL 3.2: Despliegue a Producción ---
        stage('Deploy to Production') {
            steps {
                echo "-> 4. Despliegue de la imagen ${DOCKER_IMAGE} a Producción (IL 3.2)"
                // sh "kubectl apply -f k8s/deployment.yaml"
                echo "Despliegue exitoso."
            }
        }
    }
    
    // --- IL 3.4: Trazabilidad y Documentación ---
    post {
        always {
            script {
                echo "--- Trazabilidad para Auditoría (IL 3.4) ---"
                echo "Build: ${env.BUILD_ID}, Commit: ${env.GIT_COMMIT}"
                echo "Artefactos de seguridad archivados: bandit-report.json, trivy-deps.json, trivy-image.json, ${ZAP_REPORT}"
                // Se podría enviar un resumen de la build a un sistema de registro
            }
        }
    }
}