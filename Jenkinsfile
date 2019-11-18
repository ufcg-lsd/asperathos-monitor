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
        labelledShell script: 'docker network create --attachable network-monitor-$BUILD_ID', label: "Create test network"
        labelledShell script: 'docker run -t -d --privileged --network=network-monitor-$BUILD_ID -v /.kube:/.kube/ -v d54-data-monitor-$BUILD_ID:/demo-tests/d54 -v organon-data-monitor-$BUILD_ID:/demo-tests/organon --name docker-monitor-$BUILD_ID asperathos-docker', label: "Run Docker container"
        labelledShell script: """docker create --network=network-monitor-$BUILD_ID -v d54-data-monitor-$BUILD_ID:/demo-tests/d54 \
        -v organon-data-monitor-$BUILD_ID:/demo-tests/organon --name integration-tests-monitor-$BUILD_ID \
        -e DOCKER_HOST=tcp://docker-monitor-$BUILD_ID:2375 \
        -e DOCKER_HOST_URL=docker-monitor-$BUILD_ID \
        -e ASPERATHOS_URL=docker-monitor-$BUILD_ID:1500/submissions \
        -e monitor_URL=docker-monitor-$BUILD_ID:5002/visualizing  integration-tests""" , label: "Create integration tests container"
        labelledShell script: 'docker cp . integration-tests-monitor-$BUILD_ID:/integration-tests/test_env/monitor/asperathos-monitor/', label: "Copy monitor code to container"
        labelledShell script: 'docker start -i integration-tests-monitor-$BUILD_ID', label: "Run integration tests"
      }
    }
  }
  post {
    cleanup {
      labelledShell script: 'docker stop docker-monitor-$BUILD_ID || true', label: "Stop Docker container"
      labelledShell script: 'docker rm -v docker-monitor-$BUILD_ID || true', label: "Remove Docker container"
      labelledShell script: 'docker rm -v integration-tests-monitor-$BUILD_ID || true', label: "Remove integration tests container"
      labelledShell script: 'docker network rm network-monitor-$BUILD_ID || true', label: "Remove test network"
      labelledShell script: 'docker volume rm d54-data-monitor-$BUILD_ID || true', label: "Remove D5.4 volume"
      labelledShell script: 'docker volume rm organon-data-monitor-$BUILD_ID || true', label: "Remove Organon volume"
    }
    failure {
      labelledShell script: 'docker exec docker-monitor-$BUILD_ID docker logs testenv_manager_1', label: "Manager logs"
      labelledShell script: 'docker exec docker-monitor-$BUILD_ID docker logs testenv_monitor_1', label: "Monitor logs"
      labelledShell script: 'docker exec docker-monitor-$BUILD_ID docker logs testenv_visualizer_1', label: "Visualizer logs"
      labelledShell script: 'docker exec docker-monitor-$BUILD_ID docker logs testenv_controller_1', label: "Controller logs"
    }
  }
}
