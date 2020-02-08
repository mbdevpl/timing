pipeline {
  agent none

  stages {
    stage('Test') {
      agent { label 'x86_64' }
      steps {
        sh "python -m coverage run --branch --source . -m unittest -v"
        sh "python -m coverage xml"
      }
    }
  }

  post {
    always {
      script {
        publishCoverageGithub(
          filepath:'coverage.xml', coverageXmlType: 'cobertura',
          comparisonOption: [ value: 'optionFixedCoverage', fixedCoverage: '0.9' ], coverageRateType: 'Line')
      }
    }
  }

}
