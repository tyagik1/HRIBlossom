/**
 * @license
 * Copyright 2023 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as Blockly from 'blockly';
import {blocks as setPositionBlocks} from './blocks/set_position';
import {blocks as createSequenceBlocks} from './blocks/create_sequence';
import {blocks as createFrameBlocks} from './blocks/create_frame';
import {forBlock} from './generators/javascript';
import {javascriptGenerator} from 'blockly/javascript';
import {save, load} from './serialization';
import {toolbox} from './toolbox';
import './index.css';

// Register the blocks and generator with Blockly
Blockly.common.defineBlocks(setPositionBlocks);
Blockly.common.defineBlocks(createSequenceBlocks);
Blockly.common.defineBlocks(createFrameBlocks);
Object.assign(javascriptGenerator.forBlock, forBlock);

// Set up UI elements and inject Blockly
const codeDiv = document.getElementById('generatedCode')?.querySelector('code');
const blocklyDiv = document.getElementById('blocklyDiv');

// Global state to store animation data
let animationData: any = null;

// Make animationData accessible globally for the generated code
(window as any).animationData = animationData;

// API base URL - change this to your FastAPI server URL
const API_BASE_URL = 'http://localhost:8000';

// API Functions
async function resetRobot() {
  try {
    const response = await fetch(`${API_BASE_URL}/reset`, {
      method: 'POST',
    });
    if (response.ok) {
      alert('Robot reset successfully!');
    } else {
      alert('Failed to reset robot');
    }
  } catch (error) {
    console.error('Error resetting robot:', error);
    alert('Error connecting to robot. Make sure the server is running.');
  }
}

async function playSequence() {
  if (!animationData) {
    alert('No sequence to play. Create a sequence using the blocks first.');
    return;
  }

  try {
    // Send the animation data directly (not as JSON string)
    const response = await fetch(`${API_BASE_URL}/sequences/play`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        animation: animationData.animation,
        frame_list: animationData.frame_list,
      }),
    });
    
    if (response.ok) {
      const result = await response.json();
      const mode = result.simulation ? ' (simulation mode)' : '';
      alert(`Sequence '${result.animation}' completed successfully${mode}!\n` +
            `Frames: ${result.frame_count}`);
    } else {
      const error = await response.json();
      console.error('API Error:', error);
      alert(`Failed to play sequence: ${error.detail || 'Unknown error'}`);
    }
  } catch (error) {
    console.error('Error playing sequence:', error);
    alert('Error connecting to robot. Make sure the server is running at ' + API_BASE_URL);
  }
}

if (!blocklyDiv) {
  throw new Error(`div with id 'blocklyDiv' not found`);
}
const ws = Blockly.inject(blocklyDiv, {toolbox});

// This function shows the generated JSON in the code div
const runCode = () => {
  const code = javascriptGenerator.workspaceToCode(ws as Blockly.Workspace);
  
  // Execute the generated code to build the animation data
  if (code.trim()) {
    try {
      // Clear previous animation data
      animationData = null;
      (window as any).animationData = null;
      
      // Execute the code to build the animation data
      eval(code);
      
      // Sync the global variable
      animationData = (window as any).animationData;
      
      // Display the animation data as JSON in the code div
      if (animationData && codeDiv) {
        codeDiv.textContent = JSON.stringify(animationData, null, 2);
      } else if (codeDiv) {
        codeDiv.textContent = code;
      }
    } catch (e) {
      console.error('Error executing generated code:', e);
      if (codeDiv) {
        const errorMessage = e instanceof Error ? e.message : String(e);
        codeDiv.textContent = `Error: ${errorMessage}`;
      }
    }
  } else {
    // Clear animation data when no blocks
    animationData = null;
    (window as any).animationData = null;
    if (codeDiv) {
      codeDiv.textContent = '';
    }
  }
};

if (ws) {
  // Load the initial state from storage and run the code.
  load(ws);
  runCode();

  // Every time the workspace changes state, save the changes to storage.
  ws.addChangeListener((e: Blockly.Events.Abstract) => {
    // UI events are things like scrolling, zooming, etc.
    // No need to save after one of these.
    if (e.isUiEvent) return;
    save(ws);
  });

  // Whenever the workspace changes meaningfully, run the code again.
  ws.addChangeListener((e: Blockly.Events.Abstract) => {
    // Don't run the code when the workspace finishes loading; we're
    // already running it once when the application starts.
    // Don't run the code during drags; we might have invalid state.
    if (
      e.isUiEvent ||
      e.type == Blockly.Events.FINISHED_LOADING ||
      ws.isDragging()
    ) {
      return;
    }
    runCode();
  });
}

// Set up button event listeners
const resetBtn = document.getElementById('resetBtn');
const playBtn = document.getElementById('playBtn');

if (resetBtn) {
  resetBtn.addEventListener('click', resetRobot);
}

if (playBtn) {
  playBtn.addEventListener('click', playSequence);
}
