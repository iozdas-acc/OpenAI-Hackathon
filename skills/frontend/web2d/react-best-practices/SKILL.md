---
name: react-best-practices
description: React patterns for hooks, effects, refs, and component design with escape hatch guidance. Use when writing React components, custom hooks, or debugging Effects, stale state, or ref misuse.
---

# React Best Practices

## Pair with TypeScript
When working with React, always load both this skill and `typescript-best-practices` together. TypeScript patterns (type-first development, discriminated unions, Zod validation) apply to React code.

---

## Core Principle: Effects Are Escape Hatches

Effects let you "step outside" React to synchronize with external systems. Most component logic should NOT use Effects. Before writing an Effect, ask: **"Is there a way to do this without an Effect?"**

---

## When to Use Effects

Effects are for synchronizing with **external systems**:
- Subscribing to browser APIs (WebSocket, IntersectionObserver, resize)
- Connecting to third-party libraries not written in React
- Setting up/cleaning up event listeners on window/document
- Fetching data on mount (though prefer React Query or framework data fetching)
- Controlling non-React DOM elements (video players, maps, modals)

---

## When NOT to Use Effects

### Derived State → Calculate During Render

```tsx
// BAD
const [fullName, setFullName] = useState('')
useEffect(() => {
  setFullName(firstName + ' ' + lastName)
}, [firstName, lastName])

// GOOD
const fullName = firstName + ' ' + lastName
```

### Expensive Calculations → useMemo

```tsx
// BAD
const [visibleTodos, setVisibleTodos] = useState([])
useEffect(() => {
  setVisibleTodos(getFilteredTodos(todos, filter))
}, [todos, filter])

// GOOD
const visibleTodos = useMemo(
  () => getFilteredTodos(todos, filter),
  [todos, filter]
)
```

### Resetting State on Prop Change → Use `key`

```tsx
// BAD
function ProfilePage({ userId }) {
  const [comment, setComment] = useState('')
  useEffect(() => {
    setComment('')
  }, [userId])
}

// GOOD
function ProfilePage({ userId }) {
  return <Profile userId={userId} key={userId} />
}
// key change unmounts and remounts — state resets automatically
```

### User Event Handling → Use Event Handlers

```tsx
// BAD
useEffect(() => {
  if (product.isInCart) {
    showNotification(`Added ${product.name} to cart`)
  }
}, [product])

// GOOD
function buyProduct() {
  addToCart(product)
  showNotification(`Added ${product.name} to cart`)
}
```

### Notifying Parent of State Changes

```tsx
// BAD
useEffect(() => {
  onChange(isOn)
}, [isOn, onChange])

// GOOD: update both in event handler
function updateToggle(nextIsOn) {
  setIsOn(nextIsOn)
  onChange(nextIsOn)
}

// BEST: fully controlled component
function Toggle({ isOn, onChange }) {
  return <button onClick={() => onChange(!isOn)} />
}
```

### Effect Chains → Derive in Event Handler

```tsx
// BAD: cascading Effects
useEffect(() => {
  if (card?.gold) setGoldCardCount(c => c + 1)
}, [card])
useEffect(() => {
  if (goldCardCount > 3) { setRound(r => r + 1); setGoldCardCount(0) }
}, [goldCardCount])

// GOOD: single event handler
function handlePlaceCard(nextCard) {
  setCard(nextCard)
  if (nextCard.gold) {
    if (goldCardCount < 3) {
      setGoldCardCount(goldCardCount + 1)
    } else {
      setGoldCardCount(0)
      setRound(round + 1)
    }
  }
}
```

---

## Effect Dependencies

### Never Suppress the Linter

```tsx
// BAD
useEffect(() => {
  const id = setInterval(() => {
    setCount(count + increment)
  }, 1000)
  return () => clearInterval(id)
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [])

// GOOD: fix the code, not the linter
useEffect(() => {
  const id = setInterval(() => {
    setCount(c => c + increment)  // updater removes state dependency
  }, 1000)
  return () => clearInterval(id)
}, [increment])
```

### Move Objects/Functions Inside Effects

```tsx
// BAD: new object each render triggers Effect
const options = { serverUrl, roomId }
useEffect(() => {
  const conn = createConnection(options)
  conn.connect()
  return () => conn.disconnect()
}, [options]) // fires every render!

// GOOD
useEffect(() => {
  const options = { serverUrl, roomId }
  const conn = createConnection(options)
  conn.connect()
  return () => conn.disconnect()
}, [roomId, serverUrl])
```

### useEffectEvent for Non-Reactive Logic

```tsx
// BAD: theme change causes reconnection
useEffect(() => {
  const conn = createConnection(serverUrl, roomId)
  conn.on('connected', () => showNotification('Connected!', theme))
  conn.connect()
  return () => conn.disconnect()
}, [roomId, theme]) // reconnects on theme change

// GOOD
function ChatRoom({ roomId, theme }) {
  const onConnected = useEffectEvent(() => {
    showNotification('Connected!', theme) // reads latest theme, not reactive
  })

  useEffect(() => {
    const conn = createConnection(serverUrl, roomId)
    conn.on('connected', () => onConnected())
    conn.connect()
    return () => conn.disconnect()
  }, [roomId]) // theme no longer a dependency
}
```

### Wrap Unstable Callback Props with useEffectEvent

```tsx
// BAD: parent re-render reconnects chat
useEffect(() => {
  connection.on('message', onReceiveMessage)
  // ...
}, [roomId, onReceiveMessage]) // unstable reference

// GOOD
const onMessage = useEffectEvent(onReceiveMessage)
useEffect(() => {
  connection.on('message', onMessage)
  // ...
}, [roomId]) // stable
```

---

## Effect Cleanup

### Always Clean Up

```tsx
useEffect(() => {
  const conn = createConnection(serverUrl, roomId)
  conn.connect()
  return () => conn.disconnect() // REQUIRED
}, [roomId])

useEffect(() => {
  window.addEventListener('scroll', handleScroll)
  return () => window.removeEventListener('scroll', handleScroll) // REQUIRED
}, [])
```

### Data Fetching with Ignore Flag

```tsx
useEffect(() => {
  let ignore = false

  async function fetchData() {
    const result = await fetchTodos(userId)
    if (!ignore) setTodos(result)
  }

  fetchData()
  return () => { ignore = true }
}, [userId])
```

### Development Double-Fire Is Intentional

React remounts components in dev to verify cleanup. Don't suppress it:

```tsx
// BAD
const didInit = useRef(false)
useEffect(() => {
  if (didInit.current) return
  didInit.current = true
  // ...
}, [])

// GOOD: fix the cleanup instead
useEffect(() => {
  const conn = createConnection()
  conn.connect()
  return () => conn.disconnect()
}, [])
```

---

## Refs

### Use Refs for Values That Don't Affect Rendering

```tsx
// GOOD: ref for timeout ID
const timeoutRef = useRef(null)
function handleClick() {
  clearTimeout(timeoutRef.current)
  timeoutRef.current = setTimeout(() => { /* ... */ }, 1000)
}

// BAD: ref for displayed value — UI won't update
const countRef = useRef(0)
countRef.current++ // silent — no re-render
```

### Never Read/Write ref.current During Render

```tsx
// BAD
function MyComponent() {
  const ref = useRef(0)
  ref.current++ // mutation during render
  return <div>{ref.current}</div> // reading during render
}

// GOOD: only in event handlers and Effects
function MyComponent() {
  const ref = useRef(0)
  function handleClick() { ref.current++ } // OK
  useEffect(() => { ref.current = someValue }, [someValue]) // OK
}
```

### Ref Callbacks for Dynamic Lists

```tsx
// BAD: can't call useRef in a loop
{items.map(item => {
  const ref = useRef(null) // violates rules of hooks
  return <li ref={ref} />
})}

// GOOD: ref callback with Map
const itemsRef = useRef(new Map())

{items.map(item => (
  <li
    key={item.id}
    ref={(node) => {
      if (node) itemsRef.current.set(item.id, node)
      else itemsRef.current.delete(item.id)
    }}
  />
))}
```

### useImperativeHandle for Controlled Exposure

```tsx
function MyInput({ ref }) {
  const realInputRef = useRef(null)

  useImperativeHandle(ref, () => ({
    focus() { realInputRef.current.focus() }
    // parent gets only focus(), not full DOM node
  }))

  return <input ref={realInputRef} />
}
```

---

## Custom Hooks

### Hooks Share Logic, Not State

```tsx
// Each call gets its own independent state instance
function StatusBar() { const isOnline = useOnlineStatus() }
function SaveButton() { const isOnline = useOnlineStatus() } // separate state
```

### Name `useXxx` Only If They Use Hooks

```tsx
// BAD: no hooks inside, shouldn't be useXxx
function useSorted(items) { return items.slice().sort() }

// GOOD
function getSorted(items) { return items.slice().sort() }

// GOOD: uses hooks, prefix correct
function useAuth() { return useContext(AuthContext) }
```

### Avoid "Lifecycle" Hooks — They Hide Dependencies

```tsx
// BAD: linter can't catch missing dependencies
function useMount(fn) {
  useEffect(() => { fn() }, [])
}

// GOOD: use useEffect directly
useEffect(() => { doSomething() }, [doSomething])
```

### Keep Custom Hooks Focused

```tsx
// GOOD: concrete, specific
useChatRoom({ serverUrl, roomId })
useOnlineStatus()
useFormInput(initialValue)

// BAD: generic lifecycle wrappers
useMount(fn)
useEffectOnce(fn)
useUpdateEffect(fn)
```

---

## Component Patterns

### Controlled vs Uncontrolled

```tsx
// Uncontrolled: component owns state
function SearchInput() {
  const [query, setQuery] = useState('')
  return <input value={query} onChange={e => setQuery(e.target.value)} />
}

// Controlled: parent owns state — more composable
function SearchInput({ query, onQueryChange }) {
  return <input value={query} onChange={e => onQueryChange(e.target.value)} />
}
```

### Prefer Composition Over Prop Drilling

```tsx
// BAD: prop drilling
<App user={user}>
  <Layout user={user}>
    <Header user={user}>
      <Avatar user={user} />
    </Header>
  </Layout>
</App>

// GOOD: composition
<App>
  <Layout>
    <Header avatar={<Avatar user={user} />} />
  </Layout>
</App>

// GOOD: context for truly global state
<UserContext.Provider value={user}>
  <App />
</UserContext.Provider>
```

### flushSync for Synchronous DOM Updates

```tsx
import { flushSync } from 'react-dom'

function handleAdd() {
  flushSync(() => {
    setTodos([...todos, newTodo])
  })
  // DOM is now updated — safe to read
  listRef.current.lastChild.scrollIntoView()
}
```

---

## Decision Tree

| Need | Solution |
|------|---------|
| Respond to user interaction | Event handler |
| Computed value from props/state | Calculate during render |
| Cached expensive calculation | `useMemo` |
| Reset state on prop change | `key` prop |
| Synchronize with external system | `useEffect` with cleanup |
| Non-reactive code in Effect | `useEffectEvent` |
| Mutable value that doesn't trigger render | `useRef` |
