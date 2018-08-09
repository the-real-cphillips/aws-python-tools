pipeline {
  agent any
  stages {
    stage('Plugin Setup') {
      steps {
        git(url: 'https://github.com/2uinc/ansible', branch: 'master')
      }
    }
  }
}