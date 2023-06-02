Service container
===

Check GraphQl view: [public](https://viewer.contextmachine.online/v2/scene/19a60c84-cf89-4e16-bd58-a465d173e50c) \
Check viewer content example: [view](https://viewer.contextmachine.online/v2/scene/19a60c84-cf89-4e16-bd58-a465d173e50c) \

## Running with docker
```bash
docker run --rm -p 0.0.0.0:4777:4777  -p 0.0.0.0:5777:5777 --tty --name cxm-pub-container cr.yandex/crpfskvn79g5ht8njq0k/contextmachine-public-example
```
Check your local [deployment](http://localhost:5777/cxm/api/v2/mfb_grid/graphql) .

### With [viewer](http://localhost:5777/cxm/api/v2/mfb_grid/graphql) 
1. Run the service as shown in the example above.
2. Pull and run cxm-viewer locally:
  ```bash
  # pull and run cxm-viewer locally
  docker run --rm -p 0.0.0.0:3000:3000 --name cxm-viewer sthv/cxm-viewer
  
  ```
3. Go to main [page](http://localhost:3000/v2/scenes) 
4. Create new scene.
5. Create new GraphQL query:
 - Set GraphQL endpoint as `http://localhost:5777/cxm/api/v2/mfb_grid/graphql` .
 - Set GraphQL query as:
  ```graphql
  query {
    mfbGrid {
      all
    }
  }
  ```
6. Run and show result. 
## Running with compose
_Sorry it is TODO_

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

