# CruiseControl Requirements Specification

## Complete Requirements List

This document maps all requirements from the English and Spanish specifications.

---

## 1. Initialization Requirements

### R1-INICIALIZACION
**Description**: speedSet must be initialized to null  
**Source**: English spec line 49, Spanish spec line 26-27  
**Test Strategy**: Verify `getSpeedSet()` returns null after constructor  
**Code Location**: Constructor  

### R2-INICIALIZACION  
**Description**: speedLimit must be initialized to null  
**Source**: English spec line 51, Spanish spec line 29-30  
**Test Strategy**: Verify `getSpeedLimit()` returns null after constructor  
**Code Location**: Constructor  

---

## 2. setSpeedSet() Method Requirements

### R3
**Description**: speedSet can adopt any positive value (strictly > 0)  
**Source**: English spec lines 60-61, Spanish spec lines 40-41  
**Test Strategy**:
- Test with value 1
- Test with value 50
- Test with value 120
**Expected Behavior**: Method completes without exception, `getSpeedSet()` returns the value  

### R4-ERROR
**Description**: When driver indicates zero or negative speedSet, throw IncorrectSpeedSetException  
**Source**: English spec lines 63-64, Spanish spec lines 43-45  
**Test Strategy**:
- Test with value 0 → expect exception
- Test with value -1 → expect exception
- Test with value -50 → expect exception
**Expected Behavior**: IncorrectSpeedSetException thrown  

### R5-ALTERNATIVO
**Description**: If driver has set speedLimit, then speedSet cannot exceed speedLimit  
**Source**: English spec lines 66-67, Spanish spec lines 47-48  
**Test Strategy**:
1. Set speedLimit to 100
2. Attempt to set speedSet to 90 → should succeed
3. Attempt to set speedSet to 100 → should succeed
4. Attempt to set speedSet to 101 → should fail (see R6)
**Expected Behavior**: speedSet accepted if ≤ speedLimit  

### R6-ERROR
**Description**: If speedSet exceeds speedLimit, throw SpeedSetAboveSpeedLimitException  
**Source**: English spec lines 69-70, Spanish spec lines 50-51  
**Test Strategy**:
1. Set speedLimit to 100
2. Attempt to set speedSet to 120 → expect exception
**Expected Behavior**: SpeedSetAboveSpeedLimitException thrown  

---

## 3. setSpeedLimit() Method Requirements

### R7
**Description**: speedLimit can take any positive value (strictly > 0)  
**Source**: English spec line 82  
**Test Strategy**:
- Test with value 1
- Test with value 80
- Test with value 150
**Expected Behavior**: Method completes without exception, `getSpeedLimit()` returns the value  

### R8-ERROR
**Description**: When driver indicates zero or negative speedLimit, throw IncorrectSpeedLimitException  
**Source**: English spec lines 84-85  
**Test Strategy**:
- Test with value 0 → expect exception
- Test with value -1 → expect exception
**Expected Behavior**: IncorrectSpeedLimitException thrown  

### R9-ERROR
**Description**: If speedSet was previously set, cannot set speedLimit → throw CannotSetSpeedLimitException  
**Source**: English spec lines 87-89  
**Test Strategy**:
1. Set speedSet to 80
2. Attempt to set speedLimit to 100 → expect exception
**Expected Behavior**: CannotSetSpeedLimitException thrown  

---

## 4. disable() Method Requirements

### R10
**Description**: After calling disable(), speedSet shall adopt the null value  
**Source**: English spec lines 100  
**Test Strategy**:
1. Set speedSet to 80
2. Call disable()
3. Verify `getSpeedSet()` returns null
**Expected Behavior**: speedSet is null  

### R11
**Description**: After calling disable(), speedLimit shall not be altered  
**Source**: English spec lines 102  
**Test Strategy**:
1. Set speedLimit to 100
2. Set speedSet to 80
3. Call disable()
4. Verify `getSpeedLimit()` still returns 100
**Expected Behavior**: speedLimit unchanged  

---

## 5. nextCommand() Method Requirements

### R12-IDLE
**Description**: If speedSet has not been initialized, return IDLE command  
**Source**: English spec lines 114-115  
**Test Strategy**:
1. Create CruiseControl without setting speedSet
2. Call nextCommand()
3. Verify response.command == Command.IDLE
**Expected Behavior**: IDLE response  

### R13-IDLE
**Description**: If CruiseControl has been disabled, return IDLE command  
**Source**: English spec lines 117-118  
**Test Strategy**:
1. Set speedSet to 80
2. Call disable()
3. Call nextCommand()
4. Verify response.command == Command.IDLE
**Expected Behavior**: IDLE response  

### R14-REDUCE
**Description**: When current speed > speedSet, return REDUCE command  
**Source**: English spec lines 122-123  
**Test Strategy**:
1. Set speedSet to 80
2. Mock speedometer to return 90
3. Call nextCommand()
4. Verify response.command == Command.REDUCE
**Expected Behavior**: REDUCE response  
**Note**: This is overridden by R15 if speed < road minimum  

### R15-INCREASE (Road Minimum Override)
**Description**: If current speed < minimum road speed, return INCREASE (not REDUCE) to avoid traffic violation  
**Source**: English spec lines 125-128  
**Test Strategy**:
1. Set speedSet to 80
2. Mock speedometer to return 60
3. Mock road minimum to 70
4. Call nextCommand()
5. Verify response.command == Command.INCREASE (not REDUCE even though 60 < 80)
**Expected Behavior**: INCREASE response  

### R16-INCREASE
**Description**: When current speed < speedSet, return INCREASE command  
**Source**: English spec lines 130-131  
**Test Strategy**:
1. Set speedSet to 80
2. Mock speedometer to return 70
3. Call nextCommand()
4. Verify response.command == Command.INCREASE
**Expected Behavior**: INCREASE response  
**Note**: Overridden by R17 and R18 in certain conditions  

### R17-REDUCE (SpeedLimit Override)
**Description**: If current speed > speedLimit, return REDUCE (even if speed < speedSet)  
**Source**: English spec lines 133-134  
**Test Strategy**:
1. Set speedLimit to 100
2. Set speedSet to 120
3. Mock speedometer to return 110
4. Call nextCommand()
5. Verify response.command == Command.REDUCE (even though 110 < 120)
**Expected Behavior**: REDUCE response  

### R18-REDUCE (Road Maximum Override)
**Description**: If current speed > maximum road speed, return REDUCE  
**Source**: English spec lines 136-137  
**Test Strategy**:
1. Set speedSet to 120
2. Mock speedometer to return 110
3. Mock road maximum to 100
4. Call nextCommand()
5. Verify response.command == Command.REDUCE
**Expected Behavior**: REDUCE response  

### R19-KEEP
**Description**: When current speed == speedSet, return KEEP command  
**Source**: English spec lines 139-140  
**Test Strategy**:
1. Set speedSet to 80
2. Mock speedometer to return 80
3. Call nextCommand()
4. Verify response.command == Command.KEEP
**Expected Behavior**: KEEP response  

---

## Requirements Priority

### Critical (Must Test)
- R1, R2: Initialization
- R3, R4: Basic setSpeedSet validation
- R7, R8: Basic setSpeedLimit validation
- R12, R13, R19: Basic nextCommand behavior

### High Priority
- R5, R6: speedSet vs speedLimit interaction
- R9: speedLimit restriction
- R10, R11: disable() behavior
- R14, R16: Basic speed control

### Medium Priority
- R15, R17, R18: Override scenarios

---

## Test Coverage Matrix

| Requirement | Method | Type | Complexity |
|------------|---------|------|-----------|
| R1 | Constructor | State | Low |
| R2 | Constructor | State | Low |
| R3 | setSpeedSet() | Normal | Low |
| R4 | setSpeedSet() | Exception | Low |
| R5 | setSpeedSet() | Conditional | Medium |
| R6 | setSpeedSet() | Exception | Medium |
| R7 | setSpeedLimit() | Normal | Low |
| R8 | setSpeedLimit() | Exception | Low |
| R9 | setSpeedLimit() | Exception | Medium |
| R10 | disable() | State | Low |
| R11 | disable() | State | Medium |
| R12 | nextCommand() | Control | Low |
| R13 | nextCommand() | Control | Medium |
| R14 | nextCommand() | Control | Medium |
| R15 | nextCommand() | Control | High |
| R16 | nextCommand() | Control | Medium |
| R17 | nextCommand() | Control | High |
| R18 | nextCommand() | Control | High |
| R19 | nextCommand() | Control | Low |
