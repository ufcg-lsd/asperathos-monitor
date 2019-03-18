pipeline {
    agent any
    stages {
        stage('Unit Python 2.7') {
            agent any
            steps {
                sh 'tox -epy27 -r'
            }
        }
        stage('Pep8') {
            agent any
            steps {
                sh 'tox -epep8'
            }
        }
        stage('Integration') {
            agent any
            steps {
                sh 'docker network create --attachable network-monitor-$BUILD_ID'
                sh 'docker run -t -d --privileged --network=network-monitor-$BUILD_ID -v /.kube:/.kube/ --name docker-monitor-$BUILD_ID asperathos-docker'
                sh 'docker create --network=network-monitor-$BUILD_ID --name integration-tests-monitor-$BUILD_ID -e DOCKER_HOST=tcp://$(docker ps -aqf "name=docker-monitor-$BUILD_ID"):2375 -e DOCKER_HOST_URL=$(docker ps -aqf "name=docker-monitor-$BUILD_ID") integration-tests'
                sh 'docker cp . integration-tests-monitor-$BUILD_ID:/integration-tests/test_env/monitor/asperathos-monitor/'
                sh 'docker start -i integration-tests-monitor-$BUILD_ID'
            }
        }
    }
    post {
        cleanup {
            sh 'docker stop docker-monitor-$BUILD_ID'
            sh 'docker rm -v docker-monitor-$BUILD_ID'
            sh 'docker rm -v integration-tests-monitor-$BUILD_ID'
            sh 'docker network rm network-monitor-$BUILD_ID'
        }
    }
}
