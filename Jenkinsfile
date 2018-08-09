pipeline {
  agent any
  stages {
    stage('Plugin Setup') {
      steps {
        git(url: 'https://github.com/2uinc/ansible', branch: 'master', credentialsId: 'a00a36b0-d902-459a-b2f5-452d29dc1cd7')
      }
    }
  }
}