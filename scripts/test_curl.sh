curl -X POST http://localhost:5000/render -H "Content-Type: application/yaml" --data-binary @- << EOF
track: DUT
year: 2023
render:
  should_render: false
  validate_render: false
  fps: 30
  samples: 32
  adaptive_sampling: true
  is_4k: true
  output: output.mp4
  max_cam_distance: 70
drivers:
- name: VER
  pos: 1
  color: '#fcd700'
- name: LEC
  pos: 2
  color: '#dc0000'
EOF
