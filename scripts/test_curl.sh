curl -X POST http://localhost:5000/render -H "Content-Type: application/yaml" --data-binary @- << EOF
track: SIN
year: 2024
render:
  should_render: true
  validate_render: false
  fps: 30
  samples: 32
  adaptive_sampling: true
  is_4k: true
  output: output.mp4
  max_cam_distance: 70
drivers:
- name: TSU
  pos: 1
  color: '#fcd700'
- name: RIC
  pos: 2
  color: '#dc0000'
EOF
