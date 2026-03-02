/**
 * @license
 * Cesium - https://github.com/CesiumGS/cesium
 * Version 1.138.0
 *
 * Copyright 2011-2022 Cesium Contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Columbus View (Pat. Pend.)
 *
 * Portions licensed separately.
 * See https://github.com/CesiumGS/cesium/blob/main/LICENSE.md for full licensing details.
 */

import{a as f}from"./chunk-E5QMTGUF.js";import"./chunk-DDBGLMEQ.js";import"./chunk-U6JBFYKT.js";import{a as u}from"./chunk-SXAD2VV3.js";import"./chunk-CRQEO57T.js";import"./chunk-ES6JV22Q.js";import"./chunk-YDE5NYTF.js";import"./chunk-D5TOOVMI.js";import"./chunk-CJG46G2U.js";import"./chunk-7RP73MB3.js";import"./chunk-6EENPWJS.js";import"./chunk-X2PTOT6Y.js";import"./chunk-EJIEM7C5.js";import"./chunk-QE72UI7G.js";import"./chunk-ADU5ZUW2.js";import"./chunk-FH6VU4JR.js";import"./chunk-7X6VBBKK.js";import"./chunk-6QWV4SU3.js";import"./chunk-7SVTN6CT.js";import"./chunk-ECDGM7QL.js";import"./chunk-J5LXPN2L.js";import"./chunk-52N5E5AP.js";import"./chunk-7N2D4RHA.js";import"./chunk-E7736HNO.js";function h(c,d){let e=f.upsampleMesh(c),t=e.vertices.buffer,i=e.indices.buffer,s=e.westIndicesSouthToNorth.buffer,o=e.southIndicesEastToWest.buffer,r=e.eastIndicesNorthToSouth.buffer,n=e.northIndicesWestToEast.buffer;return d.push(t,i,s,o,r,n),{verticesBuffer:t,indicesBuffer:i,vertexCountWithoutSkirts:e.vertexCountWithoutSkirts,indexCountWithoutSkirts:e.indexCountWithoutSkirts,encoding:e.encoding,westIndicesBuffer:s,southIndicesBuffer:o,eastIndicesBuffer:r,northIndicesBuffer:n,minimumHeight:e.minimumHeight,maximumHeight:e.maximumHeight,boundingSphere:e.boundingSphere3D,orientedBoundingBox:e.orientedBoundingBox,horizonOcclusionPoint:e.horizonOcclusionPoint}}var I=u(h);export{I as default};
