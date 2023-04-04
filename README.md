# Service container
It is a public example of basic CXM service container image.


## Running with docker
```bash
docker run --rm -p 0.0.0.0:4777:4777  -p 0.0.0.0:5777:5777 --tty --name cxm-pub-container cr.yandex/crpfskvn79g5ht8njq0k/contextmachine-public-example
```
Check GraphQl api: http://localhost:5777/cxm/api/v2/mfb_grid/graphql \
Check viewer content: https://viewer.contextmachine.online/scene/test-aa \
## Running with kube
```bash
kubectl apply --filename=<path to file>/cxm-pub-ex.yaml deployment.apps/contextmachine-public-example
```
`cxm-pub-ex.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: contextmachine-public-example
  name: contextmachine-public-example
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: contextmachine-public-example
  template:
    metadata:
      labels:
        app: contextmachine-public-example
    spec:
      containers:
      - image: cr.yandex/crpfskvn79g5ht8njq0k/contextmachine-public-example
        name: contextmachine-public-example
        ports:
        - containerPort: 4777
          protocol: TCP
        - containerPort: 5777
          protocol: TCP
        resources: {}
---
apiVersion: v1
kind: Service
metadata:
  labels:
    app: contextmachine-public-example
  name: contextmachine-public-example
  namespace: default
spec:
  ports:
    - name: http
      port: 5777
      targetPort: 5777
      protocol: TCP
    - name: rpyc
      protocol: TCP
      port: 4777
      targetPort: 4777
  selector:
    app: contextmachine-public-example
  type: ClusterIP
```

