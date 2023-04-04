const THREE = require("three");
const mygroup = new THREE.Group();
const objectLoader = new THREE.ObjectLoader()

function makeAxis(points, color, width) {
    const pts = [];
    for (let i = 0; i < points.length; i++){
        pts.push(new THREE.Vector3(points[i].x, points[i].y,points[i].z))
    }
    const geometry = new THREE.BufferGeometry().setFromPoints( pts );
    const material = new THREE.LineBasicMaterial({color:color, linewidth:width});
    const ln = new THREE.Line(geometry, material)

    mygroup.add(ln)

}
function makeAxisTwo(points, json, color, width) {
    const pts = [];
    const obj = new THREE.Object3D()
    for (let i = 0; i < points.length; i++){
        pts.push(new THREE.Vector3(points[i].x, points[i].y,points[i].z))
    }
    const geometry = new THREE.BufferGeometry().setFromPoints( pts );
    const material = new THREE.LineBasicMaterial({color:color, linewidth:width});

    const ln = new THREE.Line(geometry, material)
    obj.attach(ln)

    obj.attach(THREE.BufferGeometry.parse(JSON.stringify(json)))
    mygroup.add(obj)

}

function loadObject3D(json){
    return objectLoader.parse(json)
}
function loadJson(json){
    return JSON.parse(json)
}
