## 🏈 Fantasy Scoring Rules

These scoring rules define how raw player statistics should be converted into fantasy point values for use during training and inference (e.g., when computing targets and evaluating forecasts against historical data).

### **Passing**
| Stat | Code | Points |
|-----|------|--------|
| Passing Yards | `PY` | 0.04 per yard |
| Passing TD | `PTD` | 4 |
| 40+ yard TD pass bonus | `PTD40` | 2 |
| 50+ yard TD pass bonus | `PTD50` | 3 |
| Interceptions Thrown | `INT` | -2 |
| 2-pt Passing Conversion | `2PC` | 2 |
| 300–399 passing yards | `P300` | 2 |
| 400+ passing yards | `P400` | 4 |

### **Rushing**
| Stat | Code | Points |
|-----|------|--------|
| Rushing Yards | `RY` | 0.1 per yard |
| Rushing TD | `RTD` | 6 |
| 40+ yard TD rush bonus | `RTD40` | 2 |
| 50+ yard TD rush bonus | `RTD50` | 3 |
| 2-pt Rushing Conversion | `2PR` | 2 |
| 100–199 rushing yards | `RY100` | 2 |
| 200+ rushing yards | `RY200` | 4 |

### **Receiving**
| Stat | Code | Points |
|------|------|--------|
| Receiving Yards | `REY` | 0.1 per yard |
| Reception | `REC` | 1 |
| TD Reception | `RETD` | 6 |
| 40+ yard TD reception bonus | `RETD40` | 2 |
| 50+ yard TD reception bonus | `RETD50` | 3 |
| 2-pt Receiving Conversion | `2PRE` | 2 |
| 100–199 receiving yards | `REY100` | 2 |
| 200+ receiving yards | `REY200` | 4 |

### **Kicking**
| Stat | Code | Points |
|------|------|--------|
| PAT Made | `PAT` | 1 |
| FG Missed | `FGM` | -1 |
| FG Made (0–39 yds) | `FG0` | 3 |
| FG Made (40–49 yds) | `FG40` | 4 |
| FG Made (50–59 yds) | `FG50` | 5 |
| FG Made (60+ yds) | `FG60` | 5 |

### **Team Defense / Special Teams**
| Stat | Code | Points |
|------|------|--------|
| Kickoff Return TD | `KRTD` | 6 |
| Punt Return TD | `PRTD` | 6 |
| INT Return TD | `INTTD` | 6 |
| Fumble Return TD | `FRTD` | 6 |
| Blocked Punt/FG return TD | `BLKKRTD` | 6 |
| 2-pt Return | `2PTRET` | 2 |
| 1-pt Safety | `1PSF` | 1 |
| Sack | `SK` | 1 |
| Blocked Punt, PAT or FG | `BLKK` | 2 |
| Interception | `INT` | 2 |
| Fumble Recovered | `FR` | 2 |
| Safety | `SF` | 2 |

#### **Points Allowed**
| Points Allowed | Code | Points |
|----------------|------|--------|
| 0 | `PA0` | 5 |
| 1–6 | `PA1` | 4 |
| 7–13 | `PA7` | 3 |
| 14–17 | `PA14` | 1 |
| 28–34 | `PA28` | -1 |
| 35–45 | `PA35` | -3 |
| 46+ | `PA46` | -5 |

#### **Yards Allowed**
| Total Yards Allowed | Code | Points |
|---------------------|------|--------|
| <100 | `YA100` | 5 |
| 100–199 | `YA199` | 3 |
| 200–299 | `YA299` | 2 |
| 350–399 | `YA399` | -1 |
| 400–449 | `YA449` | -3 |
| 450–499 | `YA499` | -5 |
| 500–549 | `YA549` | -6 |
| 550+ | `YA550` | -7 |
