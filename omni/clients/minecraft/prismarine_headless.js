const fs = require('fs')
const os = require('os')
const path = require('path')
const crypto = require('crypto')
const net = require('net')
const THREE = require('three')
const Vec3 = require('vec3').Vec3
const { loadTexture, loadJSON } = require('prismarine-viewer/viewer/lib/utils')
const { EventEmitter } = require('events')
const { dispose3 } = require('prismarine-viewer/viewer/lib/dispose')
const TWEEN = require('@tweenjs/tween.js')
const { Entities } = require('prismarine-viewer/viewer/lib/entities')
const { Primitives } = require('prismarine-viewer/viewer/lib/primitives')
const { getVersion } = require('prismarine-viewer/viewer/lib/version')
const { createCanvas } = require('node-canvas-webgl/lib')
const { WorldView, getBufferFromStream } = require('prismarine-viewer/viewer')

const LOG_PATH = "D:\\Python\\Omni\\clients\\minecraft\\debug_stream.log"

function appendLog (message) {
  try {
    fs.appendFileSync(LOG_PATH, `${new Date().toISOString()} ${message}\n`)
  } catch {}
}

const originalConsoleWarn = console.warn.bind(console)
console.warn = (...args) => {
  const text = args.map(arg => String(arg)).join(' ')
  if (text.includes('THREE.WebGLRenderer: Texture is not power of two. Texture.minFilter should be set to THREE.NearestFilter or THREE.LinearFilter.')) {
    appendLog(`[three-warn] ${text}`)
    return
  }
  originalConsoleWarn(...args)
}

const WORKER_SOURCE = "const fs = require('fs')\nconst LOG_PATH = \"D:\\\\Python\\\\Omni\\\\clients\\\\minecraft\\\\debug_stream.log\"\nfunction appendLog (message) {\n  try {\n    fs.appendFileSync(LOG_PATH, `${new Date().toISOString()} ${message}\\n`)\n  } catch {}\n}\n\nconst { Vec3 } = require('vec3')\n\nconst tints = require('minecraft-data')('1.16.2').tints\n\nfor (const key of Object.keys(tints)) {\n  tints[key] = prepareTints(tints[key])\n}\n\nfunction prepareTints (tints) {\n  const map = new Map()\n  const defaultValue = tintToGl(tints.default)\n  for (let { keys, color } of tints.data) {\n    color = tintToGl(color)\n    for (const key of keys) {\n      map.set(`${key}`, color)\n    }\n  }\n  return new Proxy(map, {\n    get: (target, key) => {\n      return target.has(key) ? target.get(key) : defaultValue\n    }\n  })\n}\n\nfunction tintToGl (tint) {\n  const r = (tint >> 16) & 0xff\n  const g = (tint >> 8) & 0xff\n  const b = tint & 0xff\n  return [r / 255, g / 255, b / 255]\n}\n\nconst elemFaces = {\n  up: {\n    dir: [0, 1, 0],\n    mask1: [1, 1, 0],\n    mask2: [0, 1, 1],\n    corners: [\n      [0, 1, 1, 0, 1],\n      [1, 1, 1, 1, 1],\n      [0, 1, 0, 0, 0],\n      [1, 1, 0, 1, 0]\n    ]\n  },\n  down: {\n    dir: [0, -1, 0],\n    mask1: [1, 1, 0],\n    mask2: [0, 1, 1],\n    corners: [\n      [1, 0, 1, 0, 1],\n      [0, 0, 1, 1, 1],\n      [1, 0, 0, 0, 0],\n      [0, 0, 0, 1, 0]\n    ]\n  },\n  east: {\n    dir: [1, 0, 0],\n    mask1: [1, 1, 0],\n    mask2: [1, 0, 1],\n    corners: [\n      [1, 1, 1, 0, 0],\n      [1, 0, 1, 0, 1],\n      [1, 1, 0, 1, 0],\n      [1, 0, 0, 1, 1]\n    ]\n  },\n  west: {\n    dir: [-1, 0, 0],\n    mask1: [1, 1, 0],\n    mask2: [1, 0, 1],\n    corners: [\n      [0, 1, 0, 0, 0],\n      [0, 0, 0, 0, 1],\n      [0, 1, 1, 1, 0],\n      [0, 0, 1, 1, 1]\n    ]\n  },\n  north: {\n    dir: [0, 0, -1],\n    mask1: [1, 0, 1],\n    mask2: [0, 1, 1],\n    corners: [\n      [1, 0, 0, 0, 1],\n      [0, 0, 0, 1, 1],\n      [1, 1, 0, 0, 0],\n      [0, 1, 0, 1, 0]\n    ]\n  },\n  south: {\n    dir: [0, 0, 1],\n    mask1: [1, 0, 1],\n    mask2: [0, 1, 1],\n    corners: [\n      [0, 0, 1, 0, 1],\n      [1, 0, 1, 1, 1],\n      [0, 1, 1, 0, 0],\n      [1, 1, 1, 1, 0]\n    ]\n  }\n}\n\nfunction getLiquidRenderHeight (world, block, type) {\n  if (!block || block.type !== type) return 1 / 9\n  if (block.metadata === 0) {\n    const blockAbove = world.getBlock(block.position.offset(0, 1, 0))\n    if (blockAbove && blockAbove.type === type) return 1\n    return 8 / 9\n  }\n  return ((block.metadata >= 8 ? 8 : 7 - block.metadata) + 1) / 9\n}\n\nfunction renderLiquid (world, cursor, texture, type, biome, water, attr) {\n  const heights = []\n  for (let z = -1; z <= 1; z++) {\n    for (let x = -1; x <= 1; x++) {\n      heights.push(getLiquidRenderHeight(world, world.getBlock(cursor.offset(x, 0, z)), type))\n    }\n  }\n  const cornerHeights = [\n    Math.max(Math.max(heights[0], heights[1]), Math.max(heights[3], heights[4])),\n    Math.max(Math.max(heights[1], heights[2]), Math.max(heights[4], heights[5])),\n    Math.max(Math.max(heights[3], heights[4]), Math.max(heights[6], heights[7])),\n    Math.max(Math.max(heights[4], heights[5]), Math.max(heights[7], heights[8]))\n  ]\n\n  for (const face in elemFaces) {\n    const { dir, corners } = elemFaces[face]\n    const isUp = dir[1] === 1\n\n    const neighbor = world.getBlock(cursor.offset(...dir))\n    if (!neighbor) continue\n    if (neighbor.type === type) continue\n    if ((neighbor.isCube && !isUp) || neighbor.material === 'plant' || neighbor.getProperties().waterlogged) continue\n\n    let tint = [1, 1, 1]\n    if (water) {\n      let m = 1\n      if (Math.abs(dir[0]) > 0) m = 0.6\n      else if (Math.abs(dir[2]) > 0) m = 0.8\n      tint = tints.water[biome]\n      tint = [tint[0] * m, tint[1] * m, tint[2] * m]\n    }\n\n    const u = texture.u\n    const v = texture.v\n    const su = texture.su\n    const sv = texture.sv\n\n    for (const pos of corners) {\n      const height = cornerHeights[pos[2] * 2 + pos[0]]\n      attr.t_positions.push(\n        (pos[0] ? 1 : 0) + (cursor.x & 15) - 8,\n        (pos[1] ? height : 0) + (cursor.y & 15) - 8,\n        (pos[2] ? 1 : 0) + (cursor.z & 15) - 8)\n      attr.t_normals.push(...dir)\n      attr.t_uvs.push(pos[3] * su + u, pos[4] * sv * (pos[1] ? 1 : height) + v)\n      attr.t_colors.push(tint[0], tint[1], tint[2])\n    }\n  }\n}\n\nfunction vecadd3 (a, b) {\n  if (!b) return a\n  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]\n}\n\nfunction vecsub3 (a, b) {\n  if (!b) return a\n  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]\n}\n\nfunction matmul3 (matrix, vector) {\n  if (!matrix) return vector\n  return [\n    matrix[0][0] * vector[0] + matrix[0][1] * vector[1] + matrix[0][2] * vector[2],\n    matrix[1][0] * vector[0] + matrix[1][1] * vector[1] + matrix[1][2] * vector[2],\n    matrix[2][0] * vector[0] + matrix[2][1] * vector[1] + matrix[2][2] * vector[2]\n  ]\n}\n\nfunction matmulmat3 (a, b) {\n  const te = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]\n\n  const a11 = a[0][0]; const a12 = a[1][0]; const a13 = a[2][0]\n  const a21 = a[0][1]; const a22 = a[1][1]; const a23 = a[2][1]\n  const a31 = a[0][2]; const a32 = a[1][2]; const a33 = a[2][2]\n\n  const b11 = b[0][0]; const b12 = b[1][0]; const b13 = b[2][0]\n  const b21 = b[0][1]; const b22 = b[1][1]; const b23 = b[2][1]\n  const b31 = b[0][2]; const b32 = b[1][2]; const b33 = b[2][2]\n\n  te[0][0] = a11 * b11 + a12 * b21 + a13 * b31\n  te[1][0] = a11 * b12 + a12 * b22 + a13 * b32\n  te[2][0] = a11 * b13 + a12 * b23 + a13 * b33\n\n  te[0][1] = a21 * b11 + a22 * b21 + a23 * b31\n  te[1][1] = a21 * b12 + a22 * b22 + a23 * b32\n  te[2][1] = a21 * b13 + a22 * b23 + a23 * b33\n\n  te[0][2] = a31 * b11 + a32 * b21 + a33 * b31\n  te[1][2] = a31 * b12 + a32 * b22 + a33 * b32\n  te[2][2] = a31 * b13 + a32 * b23 + a33 * b33\n\n  return te\n}\n\nfunction buildRotationMatrix (axis, degree) {\n  const radians = degree / 180 * Math.PI\n  const cos = Math.cos(radians)\n  const sin = Math.sin(radians)\n\n  const axis0 = { x: 0, y: 1, z: 2 }[axis]\n  const axis1 = (axis0 + 1) % 3\n  const axis2 = (axis0 + 2) % 3\n\n  const matrix = [\n    [0, 0, 0],\n    [0, 0, 0],\n    [0, 0, 0]\n  ]\n\n  matrix[axis0][axis0] = 1\n  matrix[axis1][axis1] = cos\n  matrix[axis1][axis2] = -sin\n  matrix[axis2][axis1] = +sin\n  matrix[axis2][axis2] = cos\n\n  return matrix\n}\n\nfunction renderElement (world, cursor, element, doAO, attr, globalMatrix, globalShift, block, biome) {\n  const cullIfIdentical = block.name.indexOf('glass') >= 0\n\n  for (const face in element.faces) {\n    const eFace = element.faces[face]\n    const { corners, mask1, mask2 } = elemFaces[face]\n    const dir = matmul3(globalMatrix, elemFaces[face].dir)\n\n    if (eFace.cullface) {\n      const neighbor = world.getBlock(cursor.plus(new Vec3(...dir)))\n      if (!neighbor) continue\n      if (cullIfIdentical && neighbor.type === block.type) continue\n      if (!neighbor.transparent && neighbor.isCube) continue\n    }\n\n    const minx = element.from[0]\n    const miny = element.from[1]\n    const minz = element.from[2]\n    const maxx = element.to[0]\n    const maxy = element.to[1]\n    const maxz = element.to[2]\n\n    const u = eFace.texture.u\n    const v = eFace.texture.v\n    const su = eFace.texture.su\n    const sv = eFace.texture.sv\n\n    const ndx = Math.floor(attr.positions.length / 3)\n\n    let tint = [1, 1, 1]\n    if (eFace.tintindex !== undefined) {\n      if (eFace.tintindex === 0) {\n        if (block.name === 'redstone_wire') {\n          tint = tints.redstone[`${block.getProperties().power}`]\n        } else if (block.name === 'birch_leaves' ||\n          block.name === 'spruce_leaves' ||\n          block.name === 'lily_pad') {\n          tint = tints.constant[block.name]\n        } else if (block.name.includes('leaves') || block.name === 'vine') {\n          tint = tints.foliage[biome]\n        } else {\n          tint = tints.grass[biome]\n        }\n      }\n    }\n\n    const r = eFace.rotation || 0\n    const uvcs = Math.cos(r * Math.PI / 180)\n    const uvsn = -Math.sin(r * Math.PI / 180)\n\n    let localMatrix = null\n    let localShift = null\n\n    if (element.rotation) {\n      localMatrix = buildRotationMatrix(\n        element.rotation.axis,\n        element.rotation.angle\n      )\n\n      localShift = vecsub3(\n        element.rotation.origin,\n        matmul3(\n          localMatrix,\n          element.rotation.origin\n        )\n      )\n    }\n\n    const aos = []\n    for (const pos of corners) {\n      let vertex = [\n        (pos[0] ? maxx : minx),\n        (pos[1] ? maxy : miny),\n        (pos[2] ? maxz : minz)\n      ]\n\n      vertex = vecadd3(matmul3(localMatrix, vertex), localShift)\n      vertex = vecadd3(matmul3(globalMatrix, vertex), globalShift)\n      vertex = vertex.map(v => v / 16)\n\n      attr.positions.push(\n        vertex[0] + (cursor.x & 15) - 8,\n        vertex[1] + (cursor.y & 15) - 8,\n        vertex[2] + (cursor.z & 15) - 8\n      )\n\n      attr.normals.push(...dir)\n\n      const baseu = (pos[3] - 0.5) * uvcs - (pos[4] - 0.5) * uvsn + 0.5\n      const basev = (pos[3] - 0.5) * uvsn + (pos[4] - 0.5) * uvcs + 0.5\n      attr.uvs.push(baseu * su + u, basev * sv + v)\n\n      let light = 1\n      if (doAO) {\n        const dx = pos[0] * 2 - 1\n        const dy = pos[1] * 2 - 1\n        const dz = pos[2] * 2 - 1\n        const cornerDir = matmul3(globalMatrix, [dx, dy, dz])\n        const side1Dir = matmul3(globalMatrix, [dx * mask1[0], dy * mask1[1], dz * mask1[2]])\n        const side2Dir = matmul3(globalMatrix, [dx * mask2[0], dy * mask2[1], dz * mask2[2]])\n        const side1 = world.getBlock(cursor.offset(...side1Dir))\n        const side2 = world.getBlock(cursor.offset(...side2Dir))\n        const corner = world.getBlock(cursor.offset(...cornerDir))\n\n        const side1Block = (side1 && side1.isCube) ? 1 : 0\n        const side2Block = (side2 && side2.isCube) ? 1 : 0\n        const cornerBlock = (corner && corner.isCube) ? 1 : 0\n\n        const ao = (side1Block && side2Block) ? 0 : (3 - (side1Block + side2Block + cornerBlock))\n        light = (ao + 1) / 4\n        aos.push(ao)\n      }\n\n      attr.colors.push(tint[0] * light, tint[1] * light, tint[2] * light)\n    }\n\n    if (doAO && aos[0] + aos[3] >= aos[1] + aos[2]) {\n      attr.indices.push(\n        ndx, ndx + 3, ndx + 2,\n        ndx, ndx + 1, ndx + 3\n      )\n    } else {\n      attr.indices.push(\n        ndx, ndx + 1, ndx + 2,\n        ndx + 2, ndx + 1, ndx + 3\n      )\n    }\n  }\n}\n\nfunction getSectionGeometry (sx, sy, sz, world, blocksStates) {\n  const attr = {\n    sx: sx + 8,\n    sy: sy + 8,\n    sz: sz + 8,\n    positions: [],\n    normals: [],\n    colors: [],\n    uvs: [],\n    t_positions: [],\n    t_normals: [],\n    t_colors: [],\n    t_uvs: [],\n    indices: []\n  }\n\n  const cursor = new Vec3(0, 0, 0)\n  for (cursor.y = sy; cursor.y < sy + 16; cursor.y++) {\n    for (cursor.z = sz; cursor.z < sz + 16; cursor.z++) {\n      for (cursor.x = sx; cursor.x < sx + 16; cursor.x++) {\n        const block = world.getBlock(cursor)\n        const biome = block.biome.name\n        if (block.variant === undefined) {\n          block.variant = getModelVariants(block, blocksStates)\n        }\n\n        const positionsBefore = attr.positions.length\n        const transparentBefore = attr.t_positions.length\n\n        for (const variant of block.variant) {\n          if (!variant || !variant.model) continue\n\n          if (block.name === 'water') {\n            renderLiquid(world, cursor, variant.model.textures.particle, block.type, biome, true, attr)\n          } else if (block.name === 'lava') {\n            renderLiquid(world, cursor, variant.model.textures.particle, block.type, biome, false, attr)\n          } else {\n            let globalMatrix = null\n            let globalShift = null\n\n            for (const axis of ['x', 'y', 'z']) {\n              if (axis in variant) {\n                if (!globalMatrix) globalMatrix = buildRotationMatrix(axis, -variant[axis])\n                else globalMatrix = matmulmat3(globalMatrix, buildRotationMatrix(axis, -variant[axis]))\n              }\n            }\n\n            if (globalMatrix) {\n              globalShift = [8, 8, 8]\n              globalShift = vecsub3(globalShift, matmul3(globalMatrix, globalShift))\n            }\n\n            for (const element of variant.model.elements) {\n              renderElement(world, cursor, element, variant.model.ao, attr, globalMatrix, globalShift, block, biome)\n            }\n          }\n        }\n\n        if (attr.positions.length === positionsBefore && attr.t_positions.length === transparentBefore) {\n          const fallbackVariants = getSpecialBlockFallbackVariants(block, blocksStates)\n          for (const variant of fallbackVariants) {\n            if (!variant || !variant.model) continue\n\n            let globalMatrix = null\n            let globalShift = null\n            for (const axis of ['x', 'y', 'z']) {\n              if (axis in variant) {\n                if (!globalMatrix) globalMatrix = buildRotationMatrix(axis, -variant[axis])\n                else globalMatrix = matmulmat3(globalMatrix, buildRotationMatrix(axis, -variant[axis]))\n              }\n            }\n            if (globalMatrix) {\n              globalShift = [8, 8, 8]\n              globalShift = vecsub3(globalShift, matmul3(globalMatrix, globalShift))\n            }\n\n            for (const element of variant.model.elements) {\n              renderElement(world, cursor, element, variant.model.ao, attr, globalMatrix, globalShift, block, biome)\n            }\n          }\n        }\n      }\n    }\n  }\n\n  let ndx = attr.positions.length / 3\n  for (let i = 0; i < attr.t_positions.length / 12; i++) {\n    attr.indices.push(\n      ndx, ndx + 1, ndx + 2,\n      ndx + 2, ndx + 1, ndx + 3,\n      ndx, ndx + 2, ndx + 1,\n      ndx + 2, ndx + 3, ndx + 1\n    )\n    ndx += 4\n  }\n\n  attr.positions.push(...attr.t_positions)\n  attr.normals.push(...attr.t_normals)\n  attr.colors.push(...attr.t_colors)\n  attr.uvs.push(...attr.t_uvs)\n\n  delete attr.t_positions\n  delete attr.t_normals\n  delete attr.t_colors\n  delete attr.t_uvs\n\n  attr.positions = new Float32Array(attr.positions)\n  attr.normals = new Float32Array(attr.normals)\n  attr.colors = new Float32Array(attr.colors)\n  attr.uvs = new Float32Array(attr.uvs)\n\n  return attr\n}\n\n\nfunction pickFirstVariant (state) {\n  if (!state) return []\n  if (state.variants) {\n    for (const variant of Object.values(state.variants)) {\n      if (variant instanceof Array) return variant.length ? [variant[0]] : []\n      return [variant]\n    }\n  }\n  if (state.multipart) {\n    let variants = []\n    for (const part of state.multipart) {\n      if (part.apply instanceof Array) variants = variants.concat(part.apply)\n      else variants.push(part.apply)\n    }\n    return variants\n  }\n  return []\n}\n\nfunction getFirstExistingVariant (blockStates, candidates) {\n  for (const candidate of candidates) {\n    if (!candidate) continue\n    const variants = pickFirstVariant(blockStates[candidate])\n    if (variants.length > 0) return variants\n  }\n  return []\n}\n\nfunction getSpecialBlockFallbackVariants (block, blockStates) {\n  if (block.name === 'chest' || block.name === 'trapped_chest') {\n    return getFirstExistingVariant(blockStates, ['barrel', 'oak_planks'])\n  }\n  if (block.name === 'ender_chest') {\n    return getFirstExistingVariant(blockStates, ['obsidian'])\n  }\n  if (block.name.endsWith('_shulker_box') || block.name === 'shulker_box') {\n    const colorPrefix = block.name === 'shulker_box' ? 'purple' : block.name.replace('_shulker_box', '')\n    return getFirstExistingVariant(blockStates, [`${colorPrefix}_concrete`, `${colorPrefix}_wool`, 'purple_concrete'])\n  }\n  if (block.name.endsWith('_sign') || block.name.endsWith('_wall_sign') || block.name.endsWith('_hanging_sign') || block.name.endsWith('_wall_hanging_sign')) {\n    const woodPrefix = block.name\n      .replace('_wall_hanging_sign', '')\n      .replace('_hanging_sign', '')\n      .replace('_wall_sign', '')\n      .replace('_sign', '')\n    return getFirstExistingVariant(blockStates, [`${woodPrefix}_planks`, 'oak_planks'])\n  }\n  if (block.name.endsWith('_banner') || block.name.endsWith('_wall_banner')) {\n    const colorPrefix = block.name.replace('_wall_banner', '').replace('_banner', '')\n    return getFirstExistingVariant(blockStates, [`${colorPrefix}_wool`, 'white_wool'])\n  }\n  if (block.name.endsWith('_bed')) {\n    const colorPrefix = block.name.replace('_bed', '')\n    return getFirstExistingVariant(blockStates, [`${colorPrefix}_wool`, 'red_wool'])\n  }\n  if (block.name.endsWith('_stairs')) {\n    const base = block.name.replace('_stairs', '')\n    return getFirstExistingVariant(blockStates, [base, `${base}_planks`, `${base}_block`, 'oak_planks', 'stone'])\n  }\n  if (block.name.endsWith('_slab')) {\n    const base = block.name.replace('_slab', '')\n    return getFirstExistingVariant(blockStates, [base, `${base}_planks`, `${base}_block`, 'oak_planks', 'stone'])\n  }\n  return []\n}\n\nfunction parseProperties (properties) {\n  if (typeof properties === 'object') { return properties }\n\n  const json = {}\n  for (const prop of properties.split(',')) {\n    const [key, value] = prop.split('=')\n    json[key] = value\n  }\n  return json\n}\n\nfunction matchProperties (block, properties) {\n  if (!properties) { return true }\n\n  properties = parseProperties(properties)\n  const blockProps = block.getProperties()\n  if (properties.OR) {\n    return properties.OR.some((or) => matchProperties(block, or))\n  }\n  for (const prop in blockProps) {\n    if (typeof properties[prop] === 'string' && !properties[prop].split('|').some((value) => value === blockProps[prop] + '')) {\n      return false\n    }\n  }\n  return true\n}\n\nfunction getModelVariants (block, blockStates) {\n  if (block.name.includes('air')) return []\n\n  const state = blockStates[block.name] ?? blockStates.missing_texture\n  if (!state) return []\n  if (state.variants) {\n    for (const [properties, variant] of Object.entries(state.variants)) {\n      if (!matchProperties(block, properties)) continue\n      if (variant instanceof Array) return [variant[0]]\n      return [variant]\n    }\n  }\n  if (state.multipart) {\n    const parts = state.multipart.filter(multipart => matchProperties(block, multipart.when))\n    let variants = []\n    for (const part of parts) {\n      if (part.apply instanceof Array) {\n        variants = [...variants, ...part.apply]\n      } else {\n        variants = [...variants, part.apply]\n      }\n    }\n\n    if (variants.length > 0) return variants\n  }\n\n  return []\n}\n\n\n/* global postMessage self */\n\nif (!global.self) {\n  const r = eval('require')\n  const { parentPort } = r('worker_threads')\n  global.self = parentPort\n  global.postMessage = (value, transferList) => { parentPort.postMessage(value, transferList) }\n  global.performance = r('perf_hooks').performance\n}\n\nconst { World } = require('prismarine-viewer/viewer/lib/world')\n\nlet blocksStates = null\nlet world = null\nconst dirtySections = {}\nlet loggedVersion = false\nlet loggedBlockStates = false\nlet loggedChunk = false\nlet loggedGeometry = false\n\nfunction sectionKey (x, y, z) {\n  return `${x},${y},${z}`\n}\n\nfunction getChunkSection (chunk, x, y, z) {\n  if (!chunk) return null\n  if (typeof chunk.getSection === 'function') {\n    return chunk.getSection(new Vec3(x, y, z))\n  }\n  const minY = chunk.minY ?? 0\n  return chunk.sections[(y - minY) >> 4]\n}\n\nfunction setSectionDirty (pos, value = true) {\n  const x = Math.floor(pos.x / 16) * 16\n  const y = Math.floor(pos.y / 16) * 16\n  const z = Math.floor(pos.z / 16) * 16\n  const chunk = world.getColumn(x, z)\n  const key = sectionKey(x, y, z)\n  if (!value) {\n    delete dirtySections[key]\n    postMessage({ type: 'sectionFinished', key })\n  } else if (getChunkSection(chunk, x, y, z)) {\n    dirtySections[key] = value\n  } else {\n    postMessage({ type: 'sectionFinished', key })\n  }\n}\n\nself.onmessage = ({ data }) => {\n  if (data.type === 'version') {\n    world = new World(data.version)\n    if (!loggedVersion) {\n      appendLog(`[worker] version=${data.version}`)\n      loggedVersion = true\n    }\n  } else if (data.type === 'blockStates') {\n    blocksStates = data.json\n    if (!loggedBlockStates) {\n      appendLog(`[worker] blockStates keys=${Object.keys(blocksStates || {}).length}`)\n      loggedBlockStates = true\n    }\n  } else if (data.type === 'dirty') {\n    setSectionDirty(new Vec3(data.x, data.y, data.z), data.value)\n  } else if (data.type === 'chunk') {\n    world.addColumn(data.x, data.z, data.chunk)\n    if (!loggedChunk) {\n      appendLog(`[worker] first chunk x=${data.x} z=${data.z} minY=${data.chunk?.minY} worldHeight=${data.chunk?.worldHeight} sections=${data.chunk?.sections?.length}`)\n      loggedChunk = true\n    }\n  } else if (data.type === 'unloadChunk') {\n    world.removeColumn(data.x, data.z)\n  } else if (data.type === 'blockUpdate') {\n    const loc = new Vec3(data.pos.x, data.pos.y, data.pos.z).floored()\n    world.setBlockStateId(loc, data.stateId)\n  } else if (data.type === 'reset') {\n    world = null\n    blocksStates = null\n  }\n}\n\nsetInterval(() => {\n  if (world === null || blocksStates === null) return\n  const sections = Object.keys(dirtySections)\n  if (sections.length === 0) return\n\n  for (const key of sections) {\n    let [x, y, z] = key.split(',')\n    x = parseInt(x, 10)\n    y = parseInt(y, 10)\n    z = parseInt(z, 10)\n    const chunk = world.getColumn(x, z)\n    if (getChunkSection(chunk, x, y, z)) {\n      delete dirtySections[key]\n      const geometry = getSectionGeometry(x, y, z, world, blocksStates)\n      if (!loggedGeometry) {\n        appendLog(`[worker] first geometry key=${key} positions=${geometry.positions.length} indices=${geometry.indices.length}`)\n        loggedGeometry = true\n      }\n      const transferable = [geometry.positions.buffer, geometry.normals.buffer, geometry.colors.buffer, geometry.uvs.buffer]\n      postMessage({ type: 'geometry', key, geometry }, transferable)\n    }\n    postMessage({ type: 'sectionFinished', key })\n  }\n}, 50)\n"

global.THREE = THREE
global.Worker = require('worker_threads').Worker


function mod (x, n) {
  return ((x % n) + n) % n
}

function getDefaultWorldBounds (version) {
  const match = /^(\d+)\.(\d+)(?:\.(\d+))?$/.exec(version || '')
  const minor = match ? parseInt(match[2], 10) : 0
  if (minor >= 18) {
    return { minY: -64, maxY: 320 }
  }
  return { minY: 0, maxY: 256 }
}

function getChunkVerticalBounds (chunk, version) {
  const fallback = getDefaultWorldBounds(version)
  const minY = chunk?.minY ?? fallback.minY
  const worldHeight = chunk?.worldHeight ?? (fallback.maxY - fallback.minY)
  return { minY, maxY: minY + worldHeight }
}

class PatchedWorldRenderer {
  constructor (scene, numWorkers = 4) {
    this.sectionMeshs = {}
    this.active = false
    this.version = undefined
    this.scene = scene
    this.loadedChunks = {}
    this.chunkMetadata = {}
    this.sectionsOutstanding = new Set()
    this.renderUpdateEmitter = new EventEmitter()
    this.blockStatesData = undefined
    this.texturesDataUrl = undefined
    this._loggedGeometry = false

    this.material = new THREE.MeshLambertMaterial({ vertexColors: true, transparent: true, alphaTest: 0.1 })

    this.workers = []
    for (let i = 0; i < numWorkers; i++) {
      const worker = new Worker(WORKER_SOURCE, { eval: true })
      worker.onmessage = ({ data }) => {
        if (data.type === 'geometry') {
          if (!this._loggedGeometry) {
            appendLog(`[renderer] first geometry key=${data.key} positions=${data.geometry.positions.length} indices=${data.geometry.indices.length}`)
            this._loggedGeometry = true
          }
          let mesh = this.sectionMeshs[data.key]
          if (mesh) {
            this.scene.remove(mesh)
            dispose3(mesh)
            delete this.sectionMeshs[data.key]
          }

          const chunkCoords = data.key.split(',')
          if (!this.loadedChunks[chunkCoords[0] + ',' + chunkCoords[2]]) return

          const geometry = new THREE.BufferGeometry()
          geometry.setAttribute('position', new THREE.BufferAttribute(data.geometry.positions, 3))
          geometry.setAttribute('normal', new THREE.BufferAttribute(data.geometry.normals, 3))
          geometry.setAttribute('color', new THREE.BufferAttribute(data.geometry.colors, 3))
          geometry.setAttribute('uv', new THREE.BufferAttribute(data.geometry.uvs, 2))
          geometry.setIndex(data.geometry.indices)

          mesh = new THREE.Mesh(geometry, this.material)
          mesh.position.set(data.geometry.sx, data.geometry.sy, data.geometry.sz)
          this.sectionMeshs[data.key] = mesh
          this.scene.add(mesh)
        } else if (data.type === 'sectionFinished') {
          this.sectionsOutstanding.delete(data.key)
          this.renderUpdateEmitter.emit('update')
        }
      }
      if (worker.on) worker.on('message', (data) => { worker.onmessage({ data }) })
      this.workers.push(worker)
    }
  }

  resetWorld () {
    this.active = false
    this.loadedChunks = {}
    this.chunkMetadata = {}
    for (const mesh of Object.values(this.sectionMeshs)) {
      this.scene.remove(mesh)
    }
    this.sectionMeshs = {}
    for (const worker of this.workers) {
      worker.postMessage({ type: 'reset' })
    }
  }

  setVersion (version) {
    this.version = version
    appendLog(`[renderer] setVersion ${version}`)
    this.resetWorld()
    this.active = true
    for (const worker of this.workers) {
      worker.postMessage({ type: 'version', version })
    }
    this.updateTexturesData()
  }

  updateTexturesData () {
    loadTexture(this.texturesDataUrl || `textures/${this.version}.png`, texture => {
      texture.magFilter = THREE.NearestFilter
      texture.minFilter = THREE.NearestFilter
      texture.flipY = false
      this.material.map = texture
      appendLog(`[renderer] texture loaded for ${this.version}`)
    })

    const loadBlockStates = () => {
      return new Promise(resolve => {
        if (this.blockStatesData) return resolve(this.blockStatesData)
        return loadJSON(`blocksStates/${this.version}.json`, resolve)
      })
    }
    loadBlockStates().then((blockStates) => {
      appendLog(`[renderer] block states loaded for ${this.version} keys=${Object.keys(blockStates || {}).length}`)
      for (const worker of this.workers) {
        worker.postMessage({ type: 'blockStates', json: blockStates })
      }
    })
  }

  addColumn (x, z, chunk) {
    this.loadedChunks[`${x},${z}`] = true
    this.chunkMetadata[`${x},${z}`] = getChunkVerticalBounds(chunk, this.version)
    const meta = this.chunkMetadata[`${x},${z}`]
    appendLog(`[renderer] addColumn x=${x} z=${z} minY=${meta.minY} maxY=${meta.maxY} sections=${chunk?.sections?.length}`)
    for (const worker of this.workers) {
      worker.postMessage({ type: 'chunk', x, z, chunk })
    }

    const { minY, maxY } = meta
    for (let y = minY; y < maxY; y += 16) {
      const loc = new Vec3(x, y, z)
      this.setSectionDirty(loc)
      this.setSectionDirty(loc.offset(-16, 0, 0))
      this.setSectionDirty(loc.offset(16, 0, 0))
      this.setSectionDirty(loc.offset(0, 0, -16))
      this.setSectionDirty(loc.offset(0, 0, 16))
    }
  }

  removeColumn (x, z) {
    const metadata = this.chunkMetadata[`${x},${z}`] || getDefaultWorldBounds(this.version)
    delete this.loadedChunks[`${x},${z}`]
    delete this.chunkMetadata[`${x},${z}`]
    for (const worker of this.workers) {
      worker.postMessage({ type: 'unloadChunk', x, z })
    }

    for (let y = metadata.minY; y < metadata.maxY; y += 16) {
      this.setSectionDirty(new Vec3(x, y, z), false)
      const key = `${x},${y},${z}`
      const mesh = this.sectionMeshs[key]
      if (mesh) {
        this.scene.remove(mesh)
        dispose3(mesh)
      }
      delete this.sectionMeshs[key]
    }
  }

  setBlockStateId (pos, stateId) {
    for (const worker of this.workers) {
      worker.postMessage({ type: 'blockUpdate', pos, stateId })
    }
    this.setSectionDirty(pos)
    if ((pos.x & 15) === 0) this.setSectionDirty(pos.offset(-16, 0, 0))
    if ((pos.x & 15) === 15) this.setSectionDirty(pos.offset(16, 0, 0))
    if ((pos.y & 15) === 0) this.setSectionDirty(pos.offset(0, -16, 0))
    if ((pos.y & 15) === 15) this.setSectionDirty(pos.offset(0, 16, 0))
    if ((pos.z & 15) === 0) this.setSectionDirty(pos.offset(0, 0, -16))
    if ((pos.z & 15) === 15) this.setSectionDirty(pos.offset(0, 0, 16))
  }

  setSectionDirty (pos, value = true) {
    const hash = mod(Math.floor(pos.x / 16) + Math.floor(pos.y / 16) + Math.floor(pos.z / 16), this.workers.length)
    this.workers[hash].postMessage({ type: 'dirty', x: pos.x, y: pos.y, z: pos.z, value })
    this.sectionsOutstanding.add(`${Math.floor(pos.x / 16) * 16},${Math.floor(pos.y / 16) * 16},${Math.floor(pos.z / 16) * 16}`)
  }

  waitForChunksToRender () {
    return new Promise((resolve) => {
      if (this.sectionsOutstanding.size === 0) {
        resolve()
        return
      }

      const updateHandler = () => {
        if (this.sectionsOutstanding.size === 0) {
          this.renderUpdateEmitter.removeListener('update', updateHandler)
          resolve()
        }
      }
      this.renderUpdateEmitter.on('update', updateHandler)
    })
  }
}




class PatchedViewer {
  constructor (renderer) {
    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color('lightblue')

    this.ambientLight = new THREE.AmbientLight(0xcccccc)
    this.scene.add(this.ambientLight)

    this.directionalLight = new THREE.DirectionalLight(0xffffff, 0.5)
    this.directionalLight.position.set(1, 1, 0.5).normalize()
    this.directionalLight.castShadow = true
    this.scene.add(this.directionalLight)

    const size = renderer.getSize(new THREE.Vector2())
    this.camera = new THREE.PerspectiveCamera(75, size.x / size.y, 0.1, 1000)

    this.world = new PatchedWorldRenderer(this.scene)
    this.entities = new Entities(this.scene)
    this.primitives = new Primitives(this.scene, this.camera)

    this.domElement = renderer.domElement
    this.playerHeight = 1.6
    this.isSneaking = false
  }

  resetAll () {
    this.world.resetWorld()
    this.entities.clear()
    this.primitives.clear()
  }

  setVersion (version) {
    version = getVersion(version)
    if (version === null) {
      const msg = `${version} is not supported`
      console.log(msg)
      return false
    }
    appendLog(`[viewer] using version ${version}`)
    this.version = version
    this.world.setVersion(version)
    this.entities.clear()
    this.primitives.clear()
    return true
  }

  addColumn (x, z, chunk) {
    this.world.addColumn(x, z, chunk)
  }

  removeColumn (x, z) {
    this.world.removeColumn(x, z)
  }

  setBlockStateId (pos, stateId) {
    this.world.setBlockStateId(pos, stateId)
  }

  updateEntity (e) {
    this.entities.update(e)
  }

  updatePrimitive (p) {
    this.primitives.update(p)
  }

  setFirstPersonCamera (pos, yaw, pitch) {
    if (pos) {
      let y = pos.y + this.playerHeight
      if (this.isSneaking) y -= 0.3
      new TWEEN.Tween(this.camera.position).to({ x: pos.x, y, z: pos.z }, 50).start()
    }
    this.camera.rotation.set(pitch, yaw, 0, 'ZYX')
  }

  listen (emitter) {
    emitter.on('entity', (e) => {
      this.updateEntity(e)
    })

    emitter.on('primitive', (p) => {
      this.updatePrimitive(p)
    })

    emitter.on('loadChunk', ({ x, z, chunk }) => {
      this.addColumn(x, z, chunk)
    })

    emitter.on('unloadChunk', ({ x, z }) => {
      this.removeColumn(x, z)
    })

    emitter.on('blockUpdate', ({ pos, stateId }) => {
      this.setBlockStateId(new Vec3(pos.x, pos.y, pos.z), stateId)
    })

    this.domElement.addEventListener('pointerdown', (evt) => {
      const raycaster = new THREE.Raycaster()
      const mouse = new THREE.Vector2()
      mouse.x = (evt.clientX / this.domElement.clientWidth) * 2 - 1
      mouse.y = -(evt.clientY / this.domElement.clientHeight) * 2 + 1
      raycaster.setFromCamera(mouse, this.camera)
      const ray = raycaster.ray
      emitter.emit('mouseClick', { origin: ray.origin, direction: ray.direction, button: evt.button })
    })
  }

  update () {
    TWEEN.update()
  }

  async waitForChunksToRender () {
    await this.world.waitForChunksToRender()
  }
}



function shouldIgnoreEntity (entity) {
  return entity && entity.name === 'item'
}

function createFilteredBot (bot) {
  const listenerMap = new WeakMap()
  const proxy = Object.create(bot)

  Object.defineProperty(proxy, 'entities', {
    get () {
      const filtered = {}
      for (const [id, entity] of Object.entries(bot.entities || {})) {
        if (!entity || shouldIgnoreEntity(entity)) continue
        filtered[id] = entity
      }
      return filtered
    }
  })

  proxy.on = function (event, listener) {
    if (event === 'entitySpawn' || event === 'entityMoved' || event === 'entityGone') {
      const wrapped = function (entity, ...args) {
        if (shouldIgnoreEntity(entity)) return
        return listener(entity, ...args)
      }
      listenerMap.set(listener, wrapped)
      return bot.on(event, wrapped)
    }

    return bot.on(event, listener)
  }

  proxy.removeListener = function (event, listener) {
    const wrapped = listenerMap.get(listener) || listener
    return bot.removeListener(event, wrapped)
  }

  return proxy
}

function delay (ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function hasCenterColumn (bot) {
  try {
    const column = await bot.world.getColumnAt(bot.entity.position)
    return Boolean(column)
  } catch {
    return false
  }
}

async function waitForWorldReady (bot, timeoutMs = 5000) {
  if (await hasCenterColumn(bot)) {
    return
  }

  await new Promise((resolve) => {
    let done = false

    const finish = () => {
      if (done) return
      done = true
      bot.removeListener('chunkColumnLoad', onChunkColumnLoad)
      clearTimeout(timer)
      resolve()
    }

    const onChunkColumnLoad = async () => {
      if (await hasCenterColumn(bot)) {
        finish()
      }
    }

    const timer = setTimeout(finish, timeoutMs)
    bot.on('chunkColumnLoad', onChunkColumnLoad)
  })

  for (let attempt = 0; attempt < 30; attempt++) {
    if (await hasCenterColumn(bot)) {
      return
    }
    await delay(100)
  }
}

module.exports = function startFilteredHeadless (bot, options = {}) {
  appendLog(`[headless] start requested output=${options.output || '127.0.0.1:8089'} log=${LOG_PATH}`)
  const filteredBot = createFilteredBot(bot)
  const {
    output = '127.0.0.1:8089',
    frames = -1,
    width = 512,
    height = 512,
    viewDistance = 6,
    jpegOptions = {},
    reconnectDelayMs = 1500
  } = options

  const [host, port] = output.split(':')
  let stopped = false
  let frameIndex = 0
  let canvas = null
  let viewer = null
  let renderer = null
  let worldView = null
  let moveListener = null
  let reconnectTimer = null
  let currentClient = null
  let connectAttempt = 0

  const stopStream = () => {
    if (stopped) return
    stopped = true
    appendLog('[headless] stop stream')
    try {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
      if (moveListener) {
        filteredBot.removeListener('move', moveListener)
        moveListener = null
      }
      if (worldView) {
        worldView.removeListenersFromBot(filteredBot)
      }
      if (currentClient) {
        currentClient.destroy()
      }
    } catch {}
  }

  filteredBot.on('end', stopStream)

  const scheduleReconnect = () => {
    if (stopped || reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      if (!stopped) {
        connectSocket()
      }
    }, reconnectDelayMs)
  }

  const startFrameLoop = (socket) => {
    const update = () => {
      if (stopped || socket.destroyed || socket !== currentClient || !viewer || !renderer) {
        return
      }

      viewer.update()
      renderer.render(viewer.scene, viewer.camera)

      const sourceStream = canvas.createJPEGStream({
        bufsize: 4096,
        quality: 1,
        progressive: false,
        ...jpegOptions
      })

      getBufferFromStream(sourceStream).then((buffer) => {
        if (stopped || socket.destroyed || socket !== currentClient) {
          return
        }

        const sizeBuffer = new Uint8Array(4)
        const view = new DataView(sizeBuffer.buffer, 0)
        view.setUint32(0, buffer.length, true)

        try {
          socket.write(sizeBuffer)
          socket.write(buffer)
        } catch (error) {
          appendLog(`[headless] socket write failed: ${error}`)
          try {
            socket.destroy()
          } catch {}
          return
        }

        frameIndex += 1
        if (frameIndex === 1) {
          appendLog(`[headless] first frame bytes=${buffer.length}`)
        }
        if (frameIndex < frames || frames < 0) {
          setTimeout(update, 16)
        } else {
          socket.end()
        }
      }).catch((error) => {
        appendLog(`[headless] frame encode failed: ${error}`)
        if (!stopped && socket === currentClient) {
          setTimeout(update, 100)
        }
      })
    }

    update()
  }

  const connectSocket = () => {
    if (stopped || currentClient) return

    connectAttempt += 1
    const socket = new net.Socket()
    let connected = false

    socket.on('connect', () => {
      if (stopped) {
        socket.destroy()
        return
      }
      connected = true
      currentClient = socket
      frameIndex = 0
      appendLog(`[headless] tcp connected to ${host}:${port} attempt=${connectAttempt}`)
      startFrameLoop(socket)
    })

    socket.on('error', (error) => {
      appendLog(`[headless] tcp error attempt=${connectAttempt}: ${error?.code || error?.message || error}`)
    })

    socket.on('close', () => {
      if (socket === currentClient) {
        currentClient = null
      }
      appendLog(connected ? '[headless] socket closed' : `[headless] tcp connect failed attempt=${connectAttempt}`)
      if (!stopped) {
        scheduleReconnect()
      }
    })

    try {
      socket.connect(parseInt(port, 10), host)
    } catch (error) {
      appendLog(`[headless] connect threw attempt=${connectAttempt}: ${error}`)
      try {
        socket.destroy()
      } catch {}
      scheduleReconnect()
    }
  }

  const bootstrap = async () => {
    appendLog(`[headless] waiting for world ready at ${filteredBot.entity.position.x},${filteredBot.entity.position.y},${filteredBot.entity.position.z}`)
    await waitForWorldReady(filteredBot)
    appendLog(`[headless] world ready=${await hasCenterColumn(filteredBot)}`)
    if (stopped) return

    canvas = createCanvas(width, height)
    renderer = new THREE.WebGLRenderer({ canvas })
    viewer = new PatchedViewer(renderer)

    appendLog(`[headless] negotiated bot version=${filteredBot.version}`)

    if (!viewer.setVersion(filteredBot.version)) {
      throw new Error(`Unsupported bot version: ${filteredBot.version}`)
    }

    viewer.setFirstPersonCamera(filteredBot.entity.position, filteredBot.entity.yaw, filteredBot.entity.pitch)

    worldView = new WorldView(filteredBot.world, viewDistance, filteredBot.entity.position)
    viewer.listen(worldView)
    worldView.listenToBot(filteredBot)

    await worldView.init(filteredBot.entity.position)
    appendLog('[headless] worldView.init done')
    await worldView.updatePosition(filteredBot.entity.position, true)
    appendLog('[headless] worldView.updatePosition(force=true) done')
    await viewer.waitForChunksToRender()
    appendLog('[headless] waitForChunksToRender done')
    if (stopped) return

    moveListener = () => {
      viewer.setFirstPersonCamera(filteredBot.entity.position, filteredBot.entity.yaw, filteredBot.entity.pitch)
      void worldView.updatePosition(filteredBot.entity.position)
    }

    filteredBot.on('move', moveListener)
    connectSocket()
  }

  bootstrap().catch((error) => {
    appendLog(`[headless] bootstrap failed: ${error?.stack || error}`)
    scheduleReconnect()
  })

  return {
    end: stopStream,
    close: stopStream
  }
}
