node {
    def commit_id
    stage('preparation') {
        git url: 'https://github.com/OZ-01-Team3/oz-main_project-be', branch: 'develop'
        sh "git rev-parse --short HEAD > .git/commit-id"
        commit_id = readFile('.git/commit-id').trim()
    }
    stage('clone') {
        git branch: 'develop',
		credentialsId: 'github',
		url: 'https://github.com/OZ-01-Team3/oz-main_project-be'
    }
    stage('docker build & push') {
        script {
			sh 'docker build -t ysolarh/oz-main-be .'
			withDockerRegistry([credentialsId: 'dockerhub', url: 'https://index.docker.io/v1/']) {
				sh "docker push ysolarh/oz-main-be"
	        }
        }
    }
    stage('deployment') {
        script {
            sshagent(credentials: ['main-be-ssh']) {
                sh "ssh -o StrictHostKeyChecking=no ec2-user@3.35.11.90 'docker rm -f oz-main-be'"
                sh "ssh -o StrictHostKeyChecking=no ec2-user@3.35.11.90 'docker pull ysolarh/oz-main-be'"
                sh "ssh -o StrictHostKeyChecking=no ec2-user@3.35.11.90 'docker run -d -p 80:80 --name oz-main-be --network oz-main-be --log-driver=awslogs --log-opt awslogs-region=ap-northeast-2 --log-opt awslogs-group=oz-main-be --log-opt awslogs-stream=docker-django --log-opt awslogs-multiline-pattern='^INFO' ysolarh/oz-main-be:latest'"
            }
        }
    }
}
