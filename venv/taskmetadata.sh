#!/usr/bin/env bash

########################
# include the magic
########################
. demo-magic.sh -d
#DEMO_PROMPT="${GREEN}➜ ${CYAN}\W "
PROMPT_TIMEOUT=60
# hide the evidence
clear

#Get environment variables from CFN stack

pe "export ECS_CLUSTER=\$(aws cloudformation describe-stacks --stack-name x-ray --query 'Stacks[0].Outputs[?OutputKey==\`EcsClusterName\`][OutputValue] | [0][0]' --output text)"
pe "export SUBNET_ID_1=\$(aws cloudformation describe-stacks --stack-name x-ray --query 'Stacks[0].Outputs[?OutputKey==\`Subnet1\`][OutputValue] | [0][0]' --output text)"
pe "export SUBNET_ID_2=\$(aws cloudformation describe-stacks --stack-name x-ray --query 'Stacks[0].Outputs[?OutputKey==\`Subnet2\`][OutputValue] | [0][0]' --output text)"
pe "export FARGATE_SECURITY_GROUP=\$(aws cloudformation describe-stacks --stack-name x-ray --query 'Stacks[0].Outputs[?OutputKey==\`FargateSecurityGroup\`][OutputValue] | [0][0]' --output text)"
pe "export TASK_EXECUTION_ROLE_ARN=\$(aws iam get-role --role-name ecsTaskExecutionRole --query \"Role.Arn\" --output text)"

#Create task role

pe "aws iam create-role --role-name taskMetadataRole --assume-role-policy-document file://trust-pol.json"
pe "TASK_ARN=\$(aws iam create-policy --policy-name taskMetadataPolicy --policy-document file://taskmetadata-pol.json --query 'Policy.Arn' --output text)"
pe "aws iam attach-role-policy --role-name taskMetadataRole --policy-arn \$TASK_ARN"

#Create log group

pe "aws logs create-log-group --log-group-name /ecs/taskmetadata"

#Launch task

pe "./envsubst < ecs-params.yml-template > ecs-params.yml"
pe "docker build -t taskmetadata ."
pe "export TASKMETADATA_URI=\$(aws ecr describe-repositories --repository-name taskmetadata --query 'repositories[].repositoryUri' --output text)"
pe "./envsubst < docker-compose.yml-template > docker-compose.yml"
pe "ecs-cli compose --project-name taskmetadata --task-role-arn \$TASK_ARN up --region us-west-2 --launch-type FARGATE --cluster \$ECS_CLUSTER"
