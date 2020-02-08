pipeline {
  agent { label 'x86_64' }

  options {
    ansiColor('xterm')
  }

  stages {
    stage('Test') {
      steps {
        sh "python -m coverage run --branch --source . -m unittest -v"
        sh "python -m coverage xml"
      }
      post {
        always {
            script {
              if (env.CHANGE_ID) {
                publishCoverageGithub(
                  filepath:'coverage.xml', coverageXmlType: 'cobertura',
                  comparisonOption: [ value: 'optionFixedCoverage', fixedCoverage: '0.9' ], coverageRateType: 'Line')
              }
            }
        }
      }
    }
  }
}
