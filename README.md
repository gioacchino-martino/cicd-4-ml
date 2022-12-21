# CI/CD for ML with Cloud Build and Cloud Deploy

Imagine you are part of a Data science team and the IT department is the owner of self-managed K8s serving infrastructure. 
In order to deploy a model properly, you need a workflow that once the model is ready, it would test, build and release it into a staging and production environment. 
Here is where CI/CD practices come into play.
In this example, we will use Cloud Build and Cloud Deploy to build and deploy a model to a staging and production environment.

## How to use this repository

### Setup the demo environment

#### 1. Enable services
```shell
gcloud services enable aiplatform.googleapis.com\
                       notebooks.googleapis.com\
                       sourcerepo.googleapis.com \
                       cloudbuild.googleapis.com \
                       clouddeploy.googleapis.com \
                       container.googleapis.com \
                       cloudresourcemanager.googleapis.com \
                       servicenetworking.googleapis.com \
	               containerscanning.googleapis.com \
                       cloudkms.googleapis.com \
                       binaryauthorization.googleapis.com \
                       artifactregistry.googleapis.com \
                       ondemandscanning.googleapis.com
```
#### 2. Setup the environment variables
```shell
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects list --filter="$(gcloud config get-value project)" --format="value(PROJECT_NUMBER)")
REGION=europe-west1
VPC=gke-internal
PROD_SUBNET=gke-prd-int
PROD_SUBNET_CIDR="10.0.0.0/22" 
PROD_POD_SUBNET=gke-prd-int-pod
PROD_POD_SUBNET_CIDR="10.10.0.0/22"
PROD_SVC_SUBNET=gke-prd-int-svc
PROD_SVC_SUBNET_CIDR="10.100.0.0/24"
PROD_MASTER_IPV4_CIDR="172.16.1.0/28"
DEV_SUBNET=gke-dev-int
DEV_SUBNET_CIDR="10.1.0.0/22" 
DEV_POD_SUBNET=gke-dev-int-pod
DEV_POD_SUBNET_CIDR="10.20.0.0/22"
DEV_SVC_SUBNET=gke-dev-int-svc
DEV_SVC_SUBNET_CIDR="10.200.0.0/24"
DEV_MASTER_IPV4_CIDR="172.16.2.0/28"
GKE_CLUSTER_NAME=gke-bel
```
#### 3. IAM setup
Configure Cloud Build to allow modification of Cloud Deploy delivery pipelines and deploy to GKE:

```shell
gcloud projects add-iam-policy-binding --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role roles/clouddeploy.admin $(gcloud config get-value project)
gcloud projects add-iam-policy-binding --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role roles/container.developer $(gcloud config get-value project)
gcloud projects add-iam-policy-binding --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role roles/iam.serviceAccountUser $(gcloud config get-value project)
gcloud projects add-iam-policy-binding --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role roles/clouddeploy.jobRunner $(gcloud config get-value project)
gcloud projects add-iam-policy-binding --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role roles/artifactregistry.writer $(gcloud config get-value project)
gcloud projects add-iam-policy-binding --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role ​​roles/ondemandscanning.admin $(gcloud config get-value project)
gcloud projects add-iam-policy-binding --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role roles/container.admin $(gcloud config get-value project)
```

#### 4. Network
VPC and Subnets setup

```shell
gcloud compute networks create $VPC --project="$PROJECT_ID" --subnet-mode=custom --mtu=1460 --bgp-routing-mode=regional 
gcloud compute networks subnets create $PROD_SUBNET --project="$PROJECT_ID" --range="$PROD_SUBNET_CIDR" --network=$VPC --region=$REGION --secondary-range=$PROD_POD_SUBNET="$PROD_POD_SUBNET_CIDR",$PROD_SVC_SUBNET=$PROD_SVC_SUBNET_CIDR --enable-private-ip-google-access
gcloud compute networks subnets create $DEV_SUBNET --project="$PROJECT_ID" --range="$DEV_SUBNET_CIDR" --network=$VPC --region=$REGION --secondary-range=$DEV_POD_SUBNET="$DEV_POD_SUBNET_CIDR",$DEV_SVC_SUBNET=$DEV_SVC_SUBNET_CIDR --enable-private-ip-google-access
```

#### 5. GKE Setup

To deploy the production cluster

```shell
gcloud beta container --project "$PROJECT_ID" clusters create "$GKE_CLUSTER_NAME-prod" --region "$REGION" --no-enable-basic-auth --cluster-version "1.24.5-gke.600" --release-channel "regular" --machine-type "e2-standard-4" --image-type "COS_CONTAINERD" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --max-pods-per-node "110" --num-nodes "1" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-private-nodes --master-ipv4-cidr "$PROD_MASTER_IPV4_CIDR" --enable-master-global-access --enable-ip-alias --network "projects/$PROJECT_ID/global/networks/$VPC" --subnetwork "projects/$PROJECT_ID/regions/$REGION/subnetworks/$PROD_SUBNET" --cluster-secondary-range-name "$PROD_POD_SUBNET" --services-secondary-range-name "$PROD_SVC_SUBNET" --no-enable-intra-node-visibility --default-max-pods-per-node "110" --enable-dataplane-v2 --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing,NodeLocalDNS,GcePersistentDiskCsiDriver,ConfigConnector --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --enable-binauthz​ --workload-pool "$PROJECT_ID.svc.id.goog" --enable-shielded-nodes --shielded-secure-boot
```

Enable BinAuth with an update

```shell
gcloud container clusters update "$GKE_CLUSTER_NAME-prod" --enable-binauthz
```

To deploy the development cluster

```shell
gcloud beta container --project "$PROJECT_ID" clusters create "$GKE_CLUSTER_NAME-dev" --region "$REGION" --no-enable-basic-auth --cluster-version "1.24.5-gke.600" --release-channel "regular" --machine-type "e2-standard-4" --image-type "COS_CONTAINERD" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --max-pods-per-node "110" --num-nodes "1" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-private-nodes --master-ipv4-cidr "$DEV_MASTER_IPV4_CIDR" --enable-master-global-access --enable-ip-alias --network "projects/$PROJECT_ID/global/networks/$VPC" --subnetwork "projects/$PROJECT_ID/regions/$REGION/subnetworks/$DEV_SUBNET" --cluster-secondary-range-name "$DEV_POD_SUBNET" --services-secondary-range-name "$DEV_SVC_SUBNET" --no-enable-intra-node-visibility --default-max-pods-per-node "110" --enable-dataplane-v2 --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing,NodeLocalDNS,GcePersistentDiskCsiDriver,ConfigConnector --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --enable-binauthz​ --workload-pool "$PROJECT_ID.svc.id.goog" --enable-shielded-nodes --shielded-secure-boot
```

Enable BinAuth with an update

```shell
gcloud container clusters update "$GKE_CLUSTER_NAME-dev" --enable-binauthz
```

#### 6. Setup Cloud Artifact
```shell
gcloud artifacts repositories create "$DOCKER_REPO" --location=$REGION --repository-format=docker 
```

#### 7. Setup Pipeline Artifacts Bucket
```shell
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION -b on gs://$PROJECT_ID-gceme-artifacts/
```

#### 8. Setup Pipeline ML Model Bucket 
```shell
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION -b on gs://$PROJECT_ID-model/
```

#### 9. Build Binary Auth Image

```shell
git clone https://github.com/GoogleCloudPlatform/gke-binary-auth-tools ~/binauthz-tools

gcloud builds submit \
  --project "${PROJECT_ID}" \
  --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$DOCKER_REPO/cloudbuild-attestor" \
  ~/binauthz-tools
```

#### 10. Setup Binary Auth Key and Attestors

```shell
gcloud kms keyrings create "binauthz" \
  --project "${PROJECT_ID}" \
  --location "${REGION}"

gcloud kms keys create "vulnz-signer" \
  --project "${PROJECT_ID}" \
  --location "${REGION}" \
  --keyring "binauthz" \
  --purpose "asymmetric-signing" \
  --default-algorithm "rsa-sign-pkcs1-4096-sha512"


curl "https://containeranalysis.googleapis.com/v1/projects/${PROJECT_ID}/notes/?noteId=vulnz-note" \
  --request "POST" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer $(gcloud auth print-access-token)" \
  --header "X-Goog-User-Project: ${PROJECT_ID}" \
  --data-binary @- <<EOF
    {
      "name": "projects/${PROJECT_ID}/notes/vulnz-note",
      "attestation": {
        "hint": {
          "human_readable_name": "Vulnerability scan note"
        }
      }
    }
EOF


curl "https://containeranalysis.googleapis.com/v1/projects/${PROJECT_ID}/notes/vulnz-note:setIamPolicy" \
  --request POST \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer $(gcloud auth print-access-token)" \
  --header "X-Goog-User-Project: ${PROJECT_ID}" \
  --data-binary @- <<EOF
    {
      "resource": "projects/${PROJECT_ID}/notes/vulnz-note",
      "policy": {
        "bindings": [
          {
            "role": "roles/containeranalysis.notes.occurrences.viewer",
            "members": [
        "serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
            ]
          },
          {
            "role": "roles/containeranalysis.notes.attacher",
            "members": [
         "serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
            ]
          }
        ]
      }
    }
EOF
```

#### 11. Setup Binary Auth Policy
```shell
cat > ./binauthz-policy.yaml <<EOF
admissionWhitelistPatterns:
- namePattern: docker.io/istio/*
defaultAdmissionRule:
  enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
  evaluationMode: ALWAYS_DENY
globalPolicyEvaluationMode: ENABLE
clusterAdmissionRules:
  # Dev cluster
  ${REGION}.${GKE_CLUSTER_NAME}-dev:
    evaluationMode: REQUIRE_ATTESTATION
    enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
    requireAttestationsBy:
    - projects/${PROJECT_ID}/attestors/vulnz-attestor

  # Production cluster
  ${REGION}.${GKE_CLUSTER_NAME}-prod:
    evaluationMode: REQUIRE_ATTESTATION
    enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
    requireAttestationsBy:
    - projects/${PROJECT_ID}/attestors/vulnz-attestor
EOF

gcloud container binauthz policy import ./binauthz-policy.yaml \
  --project "${PROJECT_ID}"
```

#### 12. Trigger creation

```shell
gcloud pubsub topics create ml-model-update	

gcloud storage buckets notifications create gs://"${PROJECT_ID}-model"--topic=projects/${PROJECT_ID}/topics/ml-model-update --event-types=OBJECT_FINALIZE
```

## Copyrights

Every file containing source code must include copyright and license
information. This includes any JS/CSS files that you might be serving out to
browsers. (This is to help well-intentioned people avoid accidental copying that
doesn't comply with the license.)

Apache header:

    Copyright 2022 Google LLC

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
