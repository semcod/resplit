# DSL Script Examples

This directory contains examples of using the Rebuild DSL (Domain Specific Language) for automating rebuild operations.

## Running DSL Scripts

### Execute a single DSL command:
```bash
python3 -m rebuild dsl --command "walk repo:/path/to/repo days:7 deploy:docker-compose"
```

### Execute a DSL script file:
```bash
python3 -m rebuild dsl --script pipeline.dsl --execute
```

## DSL Syntax

### Basic Syntax
```
command param1:value1 param2:value2 flag1 flag2
```

### Supported Commands

#### Walk
```
walk repo:/path/to/repo days:7 deploy:docker-compose health_url:http://localhost:8003/api/health base_url:http://localhost:8003 output:.rebuild
```

#### Analyze
```
analyze repo:/path/to/repo type:duplicates min-lines:4 semantic
```

#### Evolution
```
evolution timeline:/path/to/timeline.json output:evolution.html title:"Code Evolution"
```

#### Auto-PR
```
auto-pr analysis:/path/to/analysis.json platform:github dry_run:true
```

#### Accelerator
```
accelerator repo:/path/to/repo days:30 parallel:10
```

#### Restore
```
restore endpoint:/api/health repo:/path/to/repo output:./restored
```

#### Serve
```
serve results_dir:.rebuild port:7821
```

## Example: pipeline.dsl

The `pipeline.dsl` file in this directory demonstrates a complete workflow:
1. Walk git history for 7 days
2. Analyze code for duplicates
3. Generate evolution timeline visualization
4. Create a PR with analysis results

Run it with:
```bash
python3 -m rebuild dsl --script pipeline.dsl --execute
```

## Advanced Usage

### Boolean Flags
```
walk repo:/path/to/repo days:7 dry_run replay
```

### Numeric Parameters
```
walk repo:/path/to/repo days:7 parallel:10
```

### String Parameters
```
evolution timeline:/path/to/timeline.json output:evolution.html title:"My Evolution"
```
