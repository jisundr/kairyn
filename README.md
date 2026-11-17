# kairyn

An agentic SDLC that grows with your repo.

**kairyn** is a Tagalized spelling of *cairn*: a pile of stacked stones that marks a trail. Each stage is a marker on the trail, and every run adds a stone back to your repo.

> Early setup. Commands, agents and stage templates are coming next.

## Install (Claude Code)

```
/plugin marketplace add jisundr/kairyn
/plugin install kairyn@kairyn
```

## Layout

```
.
├── .claude-plugin/marketplace.json   # marketplace entry pointing to ./plugin
├── plugin/                           # the kairyn plugin
│   └── .claude-plugin/plugin.json
└── README.md                         # docs live at the root
```

## License

MIT
