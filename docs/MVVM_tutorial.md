# MVVM Architecture Tutorial

A practical guide to implementing Model-View-ViewModel (MVVM) architecture in Svelte 5 for the AI Bridge Platform.

## Table of Contents

1. [Introduction](#1-introduction)
2. [MVVM Components](#2-mvvm-components)
3. [Layer Responsibilities](#3-layer-responsibilities)
4. [Svelte 5 Implementation](#4-svelte-5-implementation)
5. [Practical Examples](#5-practical-examples)
6. [Best Practices](#6-best-practices)
7. [Common Mistakes](#7-common-mistakes)
8. [Testing MVVM](#8-testing-mvvm)

---

## 1. Introduction

### What is MVVM?

MVVM (Model-View-ViewModel) is an architectural pattern that separates the user interface (View) from the business logic and data (Model) through an intermediary layer (ViewModel).

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    View     │◄───►│  ViewModel  │◄───►│    Model    │
│  (Svelte)   │     │  (.svelte.ts)│     │  (Types/API)│
└─────────────┘     └─────────────┘     └─────────────┘
     UI Only          Logic Layer        Data Layer
```

### Why MVVM for AI Bridge Platform?

1. **Separation of Concerns** - UI code stays clean and focused on presentation
2. **Testability** - ViewModels can be unit tested without UI
3. **Reusability** - ViewModels can be shared across components
4. **Maintainability** - Changes to UI don't affect business logic
5. **MCP-Driven Model** - New features via MCP tools don't require View changes

---

## 2. MVVM Components

### Model

The Model represents the data and business entities. In our architecture:

- TypeScript interfaces and types
- API response/request DTOs
- Domain entities

```typescript
// src/lib/models/chat.ts

export interface ChatThread {
  id: string;
  title: string;
  folderId: string | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatMessage {
  id: string;
  threadId: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  createdAt: Date;
}

export interface ToolCall {
  id: string;
  toolId: string;
  toolName: string;
  input: Record<string, unknown>;
  output: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed';
}
```

### View

The View is a Svelte component responsible only for:

- Rendering UI elements
- Capturing user interactions
- Displaying data from the ViewModel

```svelte
<!-- src/lib/components/chat/MessageList.svelte -->
<script lang="ts">
  import type { ChatMessage } from '$lib/models/chat';

  // Props from parent (provided by ViewModel)
  export let messages: ChatMessage[] = [];
  export let isLoading: boolean = false;

  // Events dispatched to parent
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function handleRetry(messageId: string) {
    dispatch('retry', { messageId });
  }
</script>

<div class="flex flex-col gap-4">
  {#each messages as message (message.id)}
    <div class="p-4 rounded-lg {message.role === 'user' ? 'bg-blue-100' : 'bg-gray-100'}">
      <p>{message.content}</p>
    </div>
  {/each}

  {#if isLoading}
    <div class="animate-pulse">Loading...</div>
  {/if}
</div>
```

### ViewModel

The ViewModel is the bridge between View and Model:

- Holds UI state
- Handles business logic
- Makes API calls
- Transforms data for the View

```typescript
// src/lib/viewmodels/chat.svelte.ts
import { chatService } from '$lib/services/chat';
import type { ChatThread, ChatMessage } from '$lib/models/chat';

export function createChatViewModel(threadId: string) {
  // Reactive state using Svelte 5 runes
  let messages = $state<ChatMessage[]>([]);
  let isLoading = $state(false);
  let error = $state<string | null>(null);
  let isStreaming = $state(false);

  // Computed/derived state
  const messageCount = $derived(messages.length);
  const hasMessages = $derived(messages.length > 0);
  const lastMessage = $derived(messages[messages.length - 1]);

  // Actions
  async function loadMessages() {
    isLoading = true;
    error = null;

    try {
      messages = await chatService.getMessages(threadId);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load messages';
    } finally {
      isLoading = false;
    }
  }

  async function sendMessage(content: string) {
    if (!content.trim()) return;

    // Optimistic update
    const tempMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      threadId,
      role: 'user',
      content,
      createdAt: new Date(),
    };
    messages = [...messages, tempMessage];

    isStreaming = true;
    error = null;

    try {
      const response = await chatService.sendMessage(threadId, content);
      // Replace temp message and add response
      messages = [
        ...messages.filter(m => m.id !== tempMessage.id),
        response.userMessage,
        response.assistantMessage,
      ];
    } catch (e) {
      // Rollback optimistic update
      messages = messages.filter(m => m.id !== tempMessage.id);
      error = e instanceof Error ? e.message : 'Failed to send message';
    } finally {
      isStreaming = false;
    }
  }

  async function regenerateResponse() {
    if (!lastMessage || lastMessage.role !== 'assistant') return;

    isStreaming = true;
    try {
      const newResponse = await chatService.regenerate(threadId);
      messages = [...messages.slice(0, -1), newResponse];
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to regenerate';
    } finally {
      isStreaming = false;
    }
  }

  // Initialize
  loadMessages();

  // Return public interface
  return {
    // State (readonly)
    get messages() { return messages; },
    get isLoading() { return isLoading; },
    get isStreaming() { return isStreaming; },
    get error() { return error; },
    get messageCount() { return messageCount; },
    get hasMessages() { return hasMessages; },

    // Actions
    sendMessage,
    regenerateResponse,
    loadMessages,
  };
}

export type ChatViewModel = ReturnType<typeof createChatViewModel>;
```

---

## 3. Layer Responsibilities

### What Goes Where?

| Layer | Responsibilities | Does NOT Do |
|-------|------------------|-------------|
| **Model** | Define data types, DTOs, interfaces | Business logic, API calls, UI |
| **View** | Render UI, capture events, display data | API calls, business logic, data transformation |
| **ViewModel** | State management, API calls, data transformation, business logic | Direct DOM manipulation, styling |

### Data Flow

```
User Action → View → ViewModel → Service → API
                         ↓
                    State Update
                         ↓
              View Re-renders (reactive)
```

---

## 4. Svelte 5 Implementation

### File Structure

```
src/lib/
├── components/          # View layer
│   ├── chat/
│   │   ├── ChatThread.svelte
│   │   ├── MessageList.svelte
│   │   └── MessageInput.svelte
│   └── common/
│       ├── Button.svelte
│       └── Modal.svelte
│
├── viewmodels/          # ViewModel layer
│   ├── chat.svelte.ts
│   ├── document.svelte.ts
│   └── folder.svelte.ts
│
├── models/              # Model layer
│   ├── chat.ts
│   ├── document.ts
│   └── user.ts
│
└── services/            # API layer (used by ViewModels)
    ├── api.ts
    ├── chat.ts
    └── document.ts
```

### Svelte 5 Runes

Svelte 5 introduces runes for reactivity, which work perfectly with MVVM:

```typescript
// ViewModel using Svelte 5 runes
export function createViewModel() {
  // $state - reactive state
  let count = $state(0);
  let items = $state<string[]>([]);

  // $derived - computed values
  const doubled = $derived(count * 2);
  const itemCount = $derived(items.length);

  // $effect - side effects
  $effect(() => {
    console.log('Count changed:', count);
  });

  // Actions
  function increment() {
    count++;
  }

  function addItem(item: string) {
    items = [...items, item];
  }

  return {
    get count() { return count; },
    get doubled() { return doubled; },
    get items() { return items; },
    get itemCount() { return itemCount; },
    increment,
    addItem,
  };
}
```

### Connecting View to ViewModel

```svelte
<!-- src/routes/chat/[id]/+page.svelte -->
<script lang="ts">
  import { page } from '$app/stores';
  import { createChatViewModel } from '$lib/viewmodels/chat.svelte';
  import MessageList from '$lib/components/chat/MessageList.svelte';
  import MessageInput from '$lib/components/chat/MessageInput.svelte';

  // Create ViewModel instance
  const vm = createChatViewModel($page.params.id);
</script>

<div class="flex flex-col h-full">
  <!-- Pass ViewModel state to View components -->
  <MessageList
    messages={vm.messages}
    isLoading={vm.isLoading}
    on:retry={(e) => vm.regenerateResponse()}
  />

  <MessageInput
    disabled={vm.isStreaming}
    on:send={(e) => vm.sendMessage(e.detail.content)}
  />

  {#if vm.error}
    <div class="text-red-500 p-4">{vm.error}</div>
  {/if}
</div>
```

---

## 5. Practical Examples

### Example 1: Document Editor

**Model:**
```typescript
// src/lib/models/document.ts
export interface Document {
  id: string;
  title: string;
  content: string;
  folderId: string | null;
  version: number;
  updatedAt: Date;
}

export interface DocumentVersion {
  version: number;
  content: string;
  createdAt: Date;
}
```

**ViewModel:**
```typescript
// src/lib/viewmodels/document.svelte.ts
import { documentService } from '$lib/services/document';
import type { Document, DocumentVersion } from '$lib/models/document';
import { debounce } from '$lib/utils/debounce';

export function createDocumentViewModel(documentId: string) {
  let document = $state<Document | null>(null);
  let versions = $state<DocumentVersion[]>([]);
  let isSaving = $state(false);
  let isDirty = $state(false);
  let error = $state<string | null>(null);

  // Auto-save with debounce
  const debouncedSave = debounce(async (content: string) => {
    if (!document) return;

    isSaving = true;
    try {
      await documentService.update(documentId, { content });
      isDirty = false;
    } catch (e) {
      error = 'Failed to save';
    } finally {
      isSaving = false;
    }
  }, 1000);

  async function loadDocument() {
    try {
      document = await documentService.get(documentId);
    } catch (e) {
      error = 'Failed to load document';
    }
  }

  function updateContent(content: string) {
    if (document) {
      document = { ...document, content };
      isDirty = true;
      debouncedSave(content);
    }
  }

  async function loadVersions() {
    try {
      versions = await documentService.getVersions(documentId);
    } catch (e) {
      error = 'Failed to load versions';
    }
  }

  async function restoreVersion(version: number) {
    try {
      document = await documentService.restore(documentId, version);
      isDirty = false;
    } catch (e) {
      error = 'Failed to restore version';
    }
  }

  loadDocument();

  return {
    get document() { return document; },
    get versions() { return versions; },
    get isSaving() { return isSaving; },
    get isDirty() { return isDirty; },
    get error() { return error; },
    updateContent,
    loadVersions,
    restoreVersion,
  };
}
```

**View:**
```svelte
<!-- src/lib/components/document/Editor.svelte -->
<script lang="ts">
  import type { Document } from '$lib/models/document';

  export let document: Document | null;
  export let isSaving: boolean = false;
  export let isDirty: boolean = false;

  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function handleInput(e: Event) {
    const target = e.target as HTMLTextAreaElement;
    dispatch('change', { content: target.value });
  }
</script>

<div class="relative h-full">
  {#if document}
    <textarea
      class="w-full h-full p-4 font-mono resize-none focus:outline-none"
      value={document.content}
      on:input={handleInput}
    />

    <div class="absolute top-2 right-2 text-sm text-gray-500">
      {#if isSaving}
        Saving...
      {:else if isDirty}
        Unsaved changes
      {:else}
        Saved
      {/if}
    </div>
  {:else}
    <div class="flex items-center justify-center h-full">
      Loading...
    </div>
  {/if}
</div>
```

### Example 2: Tool Attachment

**Model:**
```typescript
// src/lib/models/tool.ts
export interface MCPTool {
  id: string;
  name: string;
  description: string;
  isGlobal: boolean;
  isEnabled: boolean;
}

export interface ChatToolAttachment {
  chatId: string;
  toolId: string;
  attachedAt: Date;
}
```

**ViewModel:**
```typescript
// src/lib/viewmodels/tools.svelte.ts
import { toolService } from '$lib/services/tools';
import type { MCPTool } from '$lib/models/tool';

export function createToolsViewModel(chatId: string) {
  let availableTools = $state<MCPTool[]>([]);
  let attachedToolIds = $state<Set<string>>(new Set());
  let isLoading = $state(false);

  const attachedTools = $derived(
    availableTools.filter(t => attachedToolIds.has(t.id))
  );

  const unattachedTools = $derived(
    availableTools.filter(t => !attachedToolIds.has(t.id))
  );

  async function loadTools() {
    isLoading = true;
    try {
      const [tools, attached] = await Promise.all([
        toolService.listAvailable(),
        toolService.listAttached(chatId),
      ]);
      availableTools = tools;
      attachedToolIds = new Set(attached.map(a => a.toolId));
    } finally {
      isLoading = false;
    }
  }

  async function attachTool(toolId: string) {
    await toolService.attach(chatId, toolId);
    attachedToolIds = new Set([...attachedToolIds, toolId]);
  }

  async function detachTool(toolId: string) {
    await toolService.detach(chatId, toolId);
    attachedToolIds = new Set([...attachedToolIds].filter(id => id !== toolId));
  }

  function isAttached(toolId: string): boolean {
    return attachedToolIds.has(toolId);
  }

  loadTools();

  return {
    get availableTools() { return availableTools; },
    get attachedTools() { return attachedTools; },
    get unattachedTools() { return unattachedTools; },
    get isLoading() { return isLoading; },
    attachTool,
    detachTool,
    isAttached,
  };
}
```

---

## 6. Best Practices

### DO:

1. **Keep Views dumb** - Only rendering and event dispatching
   ```svelte
   <!-- Good -->
   <button on:click={() => dispatch('save')}>Save</button>

   <!-- Bad -->
   <button on:click={() => api.saveDocument(doc)}>Save</button>
   ```

2. **Use descriptive ViewModel methods**
   ```typescript
   // Good
   function markAsComplete() { ... }

   // Bad
   function update() { ... }
   ```

3. **Expose readonly state from ViewModels**
   ```typescript
   // Good - using getters
   return {
     get items() { return items; },
   };

   // Bad - exposing mutable state directly
   return { items };
   ```

4. **Handle errors in ViewModels**
   ```typescript
   // Good
   async function loadData() {
     try {
       data = await service.fetch();
     } catch (e) {
       error = 'Failed to load';
     }
   }
   ```

5. **Use derived state for computed values**
   ```typescript
   // Good
   const total = $derived(items.reduce((sum, i) => sum + i.price, 0));

   // Bad
   function getTotal() {
     return items.reduce((sum, i) => sum + i.price, 0);
   }
   ```

### DON'T:

1. **Don't import services in Views**
   ```svelte
   <!-- Bad -->
   <script>
     import { chatService } from '$lib/services/chat';
   </script>
   ```

2. **Don't put business logic in Views**
   ```svelte
   <!-- Bad -->
   <script>
     function calculateDiscount(price) {
       return price > 100 ? price * 0.9 : price;
     }
   </script>
   ```

3. **Don't mutate ViewModel state from Views**
   ```svelte
   <!-- Bad -->
   <button on:click={() => vm.items.push(newItem)}>Add</button>

   <!-- Good -->
   <button on:click={() => vm.addItem(newItem)}>Add</button>
   ```

4. **Don't create multiple ViewModel instances for same data**
   ```svelte
   <!-- Bad - creates new VM on each render -->
   {#each items as item}
     {@const vm = createItemViewModel(item.id)}
   {/each}
   ```

---

## 7. Common Mistakes

### Mistake 1: View calling API directly

```svelte
<!-- WRONG -->
<script>
  import { api } from '$lib/services/api';

  async function handleSave() {
    await api.post('/documents', { content });
  }
</script>
```

**Fix:** Move API calls to ViewModel.

### Mistake 2: Business logic in View

```svelte
<!-- WRONG -->
<script>
  function canUserEdit(user, document) {
    return user.role === 'admin' || document.ownerId === user.id;
  }
</script>

{#if canUserEdit(user, doc)}
  <button>Edit</button>
{/if}
```

**Fix:** Expose computed property from ViewModel.

```typescript
// ViewModel
const canEdit = $derived(
  user.role === 'admin' || document.ownerId === user.id
);
```

### Mistake 3: Storing UI-only state in ViewModel

```typescript
// WRONG - modal visibility is View concern
let isModalOpen = $state(false);
```

**Fix:** Keep pure UI state (modals, dropdowns) in View.

### Mistake 4: Passing entire ViewModel to child components

```svelte
<!-- WRONG -->
<ChildComponent {vm} />

<!-- RIGHT - pass only what's needed -->
<ChildComponent
  items={vm.items}
  on:delete={(e) => vm.deleteItem(e.detail.id)}
/>
```

---

## 8. Testing MVVM

### Testing ViewModels

ViewModels can be tested without any UI:

```typescript
// tests/viewmodels/chat.test.ts
import { describe, it, expect, vi } from 'vitest';
import { createChatViewModel } from '$lib/viewmodels/chat.svelte';
import { chatService } from '$lib/services/chat';

vi.mock('$lib/services/chat');

describe('ChatViewModel', () => {
  it('should load messages on init', async () => {
    const mockMessages = [
      { id: '1', content: 'Hello', role: 'user' }
    ];

    vi.mocked(chatService.getMessages).mockResolvedValue(mockMessages);

    const vm = createChatViewModel('thread-1');

    // Wait for async load
    await vi.waitFor(() => {
      expect(vm.messages).toEqual(mockMessages);
    });
  });

  it('should handle send message', async () => {
    const vm = createChatViewModel('thread-1');

    vi.mocked(chatService.sendMessage).mockResolvedValue({
      userMessage: { id: '1', content: 'Hi', role: 'user' },
      assistantMessage: { id: '2', content: 'Hello!', role: 'assistant' },
    });

    await vm.sendMessage('Hi');

    expect(chatService.sendMessage).toHaveBeenCalledWith('thread-1', 'Hi');
  });

  it('should set error on failure', async () => {
    const vm = createChatViewModel('thread-1');

    vi.mocked(chatService.sendMessage).mockRejectedValue(new Error('Network error'));

    await vm.sendMessage('Hi');

    expect(vm.error).toBe('Network error');
  });
});
```

### Testing Views

Views are tested for rendering and event handling:

```typescript
// tests/components/MessageList.test.ts
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import MessageList from '$lib/components/chat/MessageList.svelte';

describe('MessageList', () => {
  it('should render messages', () => {
    const messages = [
      { id: '1', content: 'Hello', role: 'user', createdAt: new Date() },
      { id: '2', content: 'Hi there!', role: 'assistant', createdAt: new Date() },
    ];

    render(MessageList, { props: { messages, isLoading: false } });

    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    render(MessageList, { props: { messages: [], isLoading: true } });

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
```

---

## Summary

MVVM in the AI Bridge Platform:

1. **Models** define data structures in `src/lib/models/`
2. **Views** are Svelte components in `src/lib/components/`
3. **ViewModels** handle logic in `src/lib/viewmodels/`
4. **Services** make API calls in `src/lib/services/`

Key principles:
- Views only render and dispatch events
- ViewModels own all business logic and state
- Models are pure data types
- Test ViewModels independently of UI

This architecture enables the MCP-driven feature model where new functionality is delivered through backend tools without requiring frontend changes.
