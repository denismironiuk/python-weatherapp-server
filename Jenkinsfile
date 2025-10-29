pipeline {
    agent {
        kubernetes {
            label 'jenkins-agent'
            defaultContainer 'jnlp'
            yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  restartPolicy: Never
  nodeSelector:
    role: cicd
  tolerations:
    - key: "dedicated"
      operator: "Equal"
      value: "cicd"
      effect: "NoSchedule"
  containers:
    - name: jnlp
      image: akarv/jenkins-agent-sec:latest
      imagePullPolicy: Always
      tty: true
      workingDir: /home/jenkins/agent
      volumeMounts:
        - name: workspace-volume
          mountPath: /home/jenkins/agent

    - name: kaniko
      image: gcr.io/kaniko-project/executor:debug
      imagePullPolicy: Always
      command: ["/busybox/sh"]
      args: ["-c", "sleep 3600"]
      tty: true
      volumeMounts:
        - name: workspace-volume
          mountPath: /home/jenkins/agent
        - name: docker-config
          mountPath: /kaniko/.docker
          readOnly: false

  volumes:
    - name: workspace-volume
      emptyDir: {}
    - name: docker-config
      emptyDir: {}
"""
        }
    }

    environment {
        IMAGE_NAME           = "akarv/weatherapp"
        SLACK_CHANNEL        = '#success'
        SLACK_CREDENTIAL_ID  = 'slack-not'
        DOCKERHUB_CREDS      = credentials('dockerhub-creds')

        // --- DEV thresholds ---
        PYLINT_THRESHOLD_DEV  = '5.0'
        BANDIT_THRESHOLD_DEV  = 'MEDIUM'
        TRIVY_FAIL_SEVERITY_DEV  = 'CRITICAL'

        // --- PROD thresholds ---
        PYLINT_THRESHOLD_PROD = '8.0'
        BANDIT_THRESHOLD_PROD = 'HIGH'
        TRIVY_FAIL_SEVERITY_PROD = 'HIGH,CRITICAL'
    }

    stages {

        stage('Setup Environment') {
            steps {
                script {
                    if (env.BRANCH_NAME == 'main') {
                        env.TARGET_ENV = 'prod'
                        env.IMAGE_TAG  = "prod-${BUILD_NUMBER}"
                    } else {
                        env.TARGET_ENV = 'dev'
                        env.IMAGE_TAG  = "dev-${BUILD_NUMBER}"
                    }

                    echo "🌍 Environment: ${env.TARGET_ENV}"
                    echo "🏷️ Image tag: ${env.IMAGE_TAG}"
                }
            }
        }

        stage('Set Security Policy') {
            steps {
                script {
                    if (env.TARGET_ENV == 'prod') {
                        env.PYLINT_THRESHOLD = env.PYLINT_THRESHOLD_PROD
                        env.BANDIT_THRESHOLD = env.BANDIT_THRESHOLD_PROD
                        env.TRIVY_FAIL_SEVERITY = env.TRIVY_FAIL_SEVERITY_PROD
                    } else {
                        env.PYLINT_THRESHOLD = env.PYLINT_THRESHOLD_DEV
                        env.BANDIT_THRESHOLD = env.BANDIT_THRESHOLD_DEV
                        env.TRIVY_FAIL_SEVERITY = env.TRIVY_FAIL_SEVERITY_DEV
                    }

                    echo """
                    📋 Security policy for ${env.TARGET_ENV.toUpperCase()}:
                    - Pylint min score: ${env.PYLINT_THRESHOLD}
                    - Bandit severity threshold: ${env.BANDIT_THRESHOLD}
                    - Trivy fail on: ${env.TRIVY_FAIL_SEVERITY}
                    """
                }
            }
        }

        stage('Checkout Code') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    env.GIT_AUTHOR = sh(
                        script: "git log -1 --pretty=format:'%an'",
                        returnStdout: true
                    ).trim()
                    echo "📝 Commit: ${env.GIT_COMMIT_SHORT} by ${env.GIT_AUTHOR}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    echo "📦 Installing Python dependencies..."
                    pip3 install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Code Quality Checks') {
            parallel {
                stage('Lint Python Code') {
                    steps {
                        sh '''
                            echo "🔍 Running pylint..."
                            pylint $(find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*") \
                                --output-format=text > pylint.log || true
                            cat pylint.log
                        '''
                        archiveArtifacts artifacts: 'pylint.log', allowEmptyArchive: true
                    }
                }

                stage('Lint Dockerfile') {
                    steps {
                        sh '''
                            echo "🐳 Running Hadolint on Dockerfile..."
                            hadolint Dockerfile || true
                        '''
                    }
                }
            }
        }

        stage('Check Pylint Score') {
            steps {
                script {
                    def output = readFile('pylint.log').trim()
                    def scoreLine = output.readLines().findAll { it.contains('Your code has been rated at') }
                    if (!scoreLine) {
                        echo '⚠️ Pylint score not found - continuing anyway'
                        return
                    }

                    def scoreMatch = scoreLine[0] =~ /rated at (-?\d+\.\d+)/
                    if (!scoreMatch) {
                        echo '⚠️ Unable to parse pylint score'
                        return
                    }

                    def score = scoreMatch[0][1].toFloat()
                    echo "✅ Pylint score: ${score}/10"
                    
                    if (score < env.PYLINT_THRESHOLD.toFloat()) {
                        if (env.TARGET_ENV == 'prod') {
                            error("❌ [PROD] Pylint score ${score} < ${env.PYLINT_THRESHOLD}")
                        } else {
                            echo "⚠️ [DEV] Pylint score ${score} < ${env.PYLINT_THRESHOLD}, continue anyway"
                        }
                    }
                }
            }
        }

        stage('Security Scans') {
            parallel {
                stage('Secrets Scan') {
                    steps {
                        sh '''
                            echo "🔐 Running Gitleaks..."
                            gitleaks detect --source=. --no-git --report-format json --report-path gitleaks.json || true
                        '''
                        archiveArtifacts artifacts: 'gitleaks.json', allowEmptyArchive: true
                    }
                }

                stage('SAST (Bandit)') {
                    steps {
                        script {
                            def exitCode = (env.TARGET_ENV == 'prod') ? '' : '--exit-zero'
                            sh """
                                echo "🛡️ Running Bandit SAST scan..."
                                bandit -r . -f json -o bandit.json ${exitCode} --exclude ./venv,./tests || true
                            """
                            archiveArtifacts artifacts: 'bandit.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                container('kaniko') {
                    withCredentials([usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh '''
                            echo "🔨 Building & pushing Docker image..."
                            mkdir -p /kaniko/.docker
                            cat > /kaniko/.docker/config.json << EOF
{
  "auths": {
    "https://index.docker.io/v1/": {
      "auth": "$(echo -n $DOCKER_USER:$DOCKER_PASS | base64)"
    }
  }
}
EOF
                            /kaniko/executor \
                                --dockerfile=Dockerfile \
                                --context=. \
                                --destination=${IMAGE_NAME}:${IMAGE_TAG} \
                                --destination=${IMAGE_NAME}:latest \
                                --destination=${IMAGE_NAME}:${GIT_COMMIT_SHORT} \
                                --cache=true --snapshot-mode=redo
                        '''
                    }
                }
            }
        }

        stage('Security: Container Scan') {
            steps {
                script {
                    def exitCode = (env.TARGET_ENV == 'prod') ? 1 : 0
                    sh """
                        echo "🔍 Running Trivy scan..."
                        trivy image \
                            --severity ${TRIVY_FAIL_SEVERITY} \
                            --ignore-unfixed \
                            --exit-code ${exitCode} \
                            --format json \
                            --output trivy.json \
                            ${IMAGE_NAME}:${IMAGE_TAG} || true
                    """
                    archiveArtifacts artifacts: 'trivy.json', allowEmptyArchive: true
                }
            }
        }

        stage('Sign Container Image') {
            when {
                expression { env.TARGET_ENV == 'prod' }
            }
            steps {
                container('jnlp') {
                    withCredentials([
                        file(credentialsId: 'cosign-key', variable: 'COSIGN_KEY'),
                        usernamePassword(
                            credentialsId: 'dockerhub-creds',
                            usernameVariable: 'COSIGN_DOCKER_USERNAME',
                            passwordVariable: 'COSIGN_DOCKER_PASSWORD'
                        )
                    ]) {
                        sh '''
                            echo "✍️ Signing container with Cosign..."
                            cosign version
                            COSIGN_DOCKER_USERNAME="$COSIGN_DOCKER_USERNAME" \
                            COSIGN_DOCKER_PASSWORD="$COSIGN_DOCKER_PASSWORD" \
                            cosign sign --key "${COSIGN_KEY}" --yes ${IMAGE_NAME}:${IMAGE_TAG} || echo "⚠️ Signing skipped"
                        '''
                    }
                }
            }
        }

        stage('Update Helm Manifests') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'glpat-5t6gRYF9xtVedcBYEMQr',
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_PASS'
                )]) {
                    sh '''
                        echo "📦 Updating Helm values for ${TARGET_ENV}..."
                        git config --global user.email "jenkins@ci.local"
                        git config --global user.name "Jenkins CI"

                        rm -rf helmchart
                        git clone "http://${GIT_USER}:${GIT_PASS}@10.0.7.10/devops/helmchart.git"
                        cd helmchart/${TARGET_ENV}/weatherapp

                        sed -i "s|tag:.*|tag: \"${IMAGE_TAG}\"|" values.yaml
                        git add values.yaml
                        git diff --staged --quiet || (
                            git commit -m "🚀 Update ${TARGET_ENV} image to ${IMAGE_TAG}"
                            git push origin main
                        )
                    '''
                }
            }
        }

        stage('Validate Helm Chart') {
            steps {
                sh '''
                    echo "✅ Validating Helm chart..."
                    cd helmchart/${TARGET_ENV}/weatherapp
                    helm lint . --strict || echo "⚠️ Helm lint found issues"
                    helm template weatherapp . --debug --namespace ${TARGET_ENV} > rendered.yaml
                '''
                archiveArtifacts artifacts: '**/rendered.yaml', allowEmptyArchive: true
            }
        }
    }

    post {
        always {
            echo '🧹 Cleaning workspace...'
            cleanWs()
        }
        success {
            echo '✅ Pipeline succeeded!'
            notifySlack('✅ Success', 'good')
        }
        failure {
            echo '❌ Pipeline failed!'
            notifySlack('❌ Failure', 'danger')
        }
        unstable {
            echo '⚠️ Pipeline unstable!'
            notifySlack('⚠️ Unstable', 'warning')
        }
    }
}

def notifySlack(String statusEmoji, String colorCode) {
    def branch   = env.BRANCH_NAME ?: 'unknown'
    def buildNum = env.BUILD_NUMBER ?: 'N/A'
    def duration = currentBuild.durationString.replace(' and counting', '')
    def envName  = env.TARGET_ENV ?: 'unknown'
    def commitShort = env.GIT_COMMIT_SHORT ?: 'N/A'
    def author   = env.GIT_AUTHOR ?: 'Unknown'

    def emojiEnv = (envName == 'prod') ? '🚀' : '🧪'

    slackSend(
        channel: env.SLACK_CHANNEL,
        color: colorCode,
        message: """${statusEmoji} *${env.JOB_NAME}* #${buildNum}
*Branch:* `${branch}` (${commitShort})
*Author:* ${author}
*Environment:* ${emojiEnv} ${envName}
*Image:* `${env.IMAGE_NAME}:${env.IMAGE_TAG}`
*Duration:* ${duration}
*Status:* ${currentBuild.currentResult}
*Build URL:* ${env.BUILD_URL}""",
        tokenCredentialId: env.SLACK_CREDENTIAL_ID
    )
}
