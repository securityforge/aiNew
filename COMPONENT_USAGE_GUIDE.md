# Component Usage Guide

## Overview
This guide covers the standardized UI components available in the Agent Viper frontend. Use these components instead of writing custom styles for consistency.

---

## Button Component

**File**: `src/components/shared/Button.jsx`

### Variants
- **primary** — Yellow CTA button (use for main actions)
- **secondary** — Dark button with border (use for secondary actions)
- **tertiary** — Text-only button (use for subtle actions)
- **danger** — Red button (use for destructive actions)
- **success** — Green button (use for positive confirmations)

### Sizes
- **sm** — Small: `px-3 py-1.5 text-xs`
- **md** — Medium (default): `px-4 py-2.5 text-sm`
- **lg** — Large: `px-5 py-3 text-base`

### Examples
```jsx
import { Button } from '../components/shared/Button'

// Primary button with icon
<Button variant="primary" size="md">
  <Download className="w-4 h-4" />
  Download
</Button>

// Secondary button
<Button variant="secondary">Cancel</Button>

// Danger button with loading state
<Button variant="danger" loading={isDeleting}>
  Delete
</Button>

// Tertiary (text-only)
<Button variant="tertiary">Learn more</Button>
```

---

## Card Component

**File**: `src/components/shared/CardComponent.jsx`

### Variants
- **default** — Basic card with border
- **accent** — Gradient card with accent color (cyan, green, yellow, red)
- **elevated** — Card with left border accent and shadow
- **interactive** — Hoverable card that lifts on interaction

### Examples
```jsx
import { CardComponent, CardHeader, CardContent, CardFooter } from '../components/shared/CardComponent'

// Basic card
<CardComponent>
  <h3>Card Title</h3>
  <p>Card content</p>
</CardComponent>

// Accent card (cyan)
<CardComponent variant="accent" accentColor="cyan">
  <h3>Data Card</h3>
</CardComponent>

// Elevated card (yellow)
<CardComponent variant="elevated" accentColor="yellow">
  Important content
</CardComponent>

// With header, content, footer
<CardComponent>
  <CardHeader>Header</CardHeader>
  <CardContent>Content goes here</CardContent>
  <CardFooter>
    <Button variant="primary">Save</Button>
  </CardFooter>
</CardComponent>
```

---

## Alert Component

**File**: `src/components/shared/Alert.jsx`

### Types
- **success** — Green alert (successful operations)
- **error** — Red alert (errors)
- **warning** — Yellow alert (warnings)
- **info** — Blue alert (information)

### Props
- `title` — Alert title
- `message` — Alert message
- `dismissible` — Show close button
- `onDismiss` — Callback when dismissed
- `type` — success | error | warning | info

### Examples
```jsx
import { Alert, SuccessAlert, ErrorAlert } from '../components/shared/Alert'

// Basic alert
<Alert type="success" title="Success" message="Operation completed" />

// With dismissible
<Alert
  type="error"
  title="Error"
  message={error}
  dismissible
  onDismiss={() => setError(null)}
/>

// Convenience components
<SuccessAlert title="Saved" message="Changes saved successfully" />
<ErrorAlert title="Failed" message="Operation failed" />
```

---

## Form Components

**File**: `src/components/shared/Form.jsx`

### Components
- `Form` — Form wrapper
- `FormGroup` — Group inputs with spacing
- `FormLabel` — Label with required indicator
- `FormInput` — Text input with validation
- `FormSelect` — Select dropdown
- `FormTextarea` — Textarea
- `FormCheckbox` — Checkbox input

### Examples
```jsx
import {
  Form, FormGroup, FormLabel, FormInput,
  FormSelect, FormCheckbox
} from '../components/shared/Form'

<Form onSubmit={handleSubmit}>
  <FormGroup>
    <FormLabel required>Username</FormLabel>
    <FormInput
      placeholder="Enter username"
      error={errors.username}
      helpText="3-20 characters"
    />
  </FormGroup>

  <FormGroup>
    <FormLabel>Provider</FormLabel>
    <FormSelect>
      <option>Select...</option>
      <option value="openai">OpenAI</option>
      <option value="anthropic">Anthropic</option>
    </FormSelect>
  </FormGroup>

  <FormGroup>
    <FormCheckbox
      label="Remember me"
      error={errors.remember}
    />
  </FormGroup>
</Form>
```

---

## Table Component

**File**: `src/components/shared/Table.jsx`

### Components
- `Table` — Main table wrapper
- `TableHead` — Table header
- `TableBody` — Table body
- `TableRow` — Table row with striping
- `TableHeader` — Header cell
- `TableCell` — Data cell

### Features
- Automatic striping (alternating row colors)
- Hover effects on rows
- Responsive overflow handling

### Examples
```jsx
import {
  Table, TableHead, TableBody, TableRow,
  TableHeader, TableCell
} from '../components/shared/Table'

<Table>
  <TableHead>
    <TableRow>
      <TableHeader>Name</TableHeader>
      <TableHeader align="center">Status</TableHeader>
      <TableHeader align="right">Count</TableHeader>
    </TableRow>
  </TableHead>
  <TableBody>
    {data.map(item => (
      <TableRow key={item.id}>
        <TableCell>{item.name}</TableCell>
        <TableCell align="center"><Badge severity="Success" /></TableCell>
        <TableCell align="right">{item.count}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

---

## Badge Component

**File**: `src/components/shared/BadgeNew.jsx`

### Severity Levels
- **Critical** — Red
- **High** — Orange
- **Medium** — Yellow
- **Low** — Blue
- **Info** — Cyan
- **Success** — Green
- **Pending** — Yellow (animated)
- **Failed** — Red

### Variants
- **default** — Standard badge
- **chip** — Badge with icon dot
- **dot** — Just the colored dot

### Examples
```jsx
import { Badge, CriticalBadge, SuccessBadge } from '../components/shared/BadgeNew'

// Basic badge
<Badge severity="Critical" />

// With label
<Badge severity="High" label="High Priority" />

// As chip
<Badge severity="Medium" variant="chip" label="In Progress" />

// Just dot
<Badge severity="Success" variant="dot" />

// Convenience components
<CriticalBadge />
<SuccessBadge label="Completed" />
```

---

## Skeleton (Loading) Component

**File**: `src/components/shared/Skeleton.jsx`

### Components
- `Skeleton` — Generic skeleton block
- `CardSkeleton` — Card loading state
- `TableSkeleton` — Table loading state
- `BarChartSkeleton` — Chart loading state
- `ListSkeleton` — List loading state

### Examples
```jsx
import { CardSkeleton, TableSkeleton } from '../components/shared/Skeleton'

// Show during loading
{isLoading ? (
  <CardSkeleton />
) : (
  <Card>...</Card>
)}

// Multiple items
{isLoading ? (
  <TableSkeleton rows={5} cols={4} />
) : (
  <Table>...</Table>
)}
```

---

## EmptyState Component

**File**: `src/components/shared/EmptyState.jsx`

### Props
- `icon` — Icon component
- `title` — Empty state title
- `description` — Description text
- `action` — Callback for CTA button
- `actionLabel` — Button text (default: "Take Action")

### Examples
```jsx
import { EmptyState } from '../components/shared/EmptyState'
import { Inbox } from 'lucide-react'

<EmptyState
  icon={Inbox}
  title="No data yet"
  description="Start by creating your first item"
  action={() => navigate('/create')}
  actionLabel="Create Item"
/>
```

---

## Modal Component

**File**: `src/components/shared/Modal.jsx`

### Components
- `Modal` — Modal container with backdrop
- `ModalHeader` — Modal header with title and close button
- `ModalContent` — Modal content area
- `ModalFooter` — Modal footer for actions

### Examples
```jsx
import { Modal, ModalHeader, ModalContent, ModalFooter } from '../components/shared/Modal'
import { Button } from './Button'

<Modal isOpen={isOpen} onClose={handleClose}>
  <ModalHeader title="Confirm Action" onClose={handleClose} />
  <ModalContent>
    Are you sure you want to continue?
  </ModalContent>
  <ModalFooter>
    <Button variant="secondary" onClick={handleClose}>
      Cancel
    </Button>
    <Button variant="primary" onClick={handleConfirm}>
      Confirm
    </Button>
  </ModalFooter>
</Modal>
```

---

## Breadcrumb Component

**File**: `src/components/shared/Breadcrumb.jsx`

### Examples
```jsx
import { Breadcrumb } from '../components/shared/Breadcrumb'

<Breadcrumb
  items={[
    { label: 'Home', href: '/' },
    { label: 'Findings', href: '/results?tab=findings' },
    { label: 'Critical Issues' }
  ]}
/>
```

---

## Color Palette

### Accent Colors
- **Primary Yellow**: `#FFCC00` — Use for CTAs, highlights
- **Cyan**: `#00BCD4` — Data, insights
- **Green**: `#4CAF50` — Success, positive
- **Red**: `#F44336` — Errors, critical
- **Orange**: `#FF9800` — Warnings
- **Purple**: `#9C27B0` — Analysis, insights
- **Blue**: `#2196F3` — Information

### Backgrounds
- **nexus-900**: `#0B1220` — Primary background
- **nexus-800**: `#101B2E` — Secondary background
- **nexus-700**: `#1E2A44` — Tertiary background

### Text
- **white**: Primary text
- **gray-300**: Secondary text
- **gray-400**: Tertiary text
- **gray-500**: Quaternary/muted text

---

## Best Practices

### 1. Consistency
- Always use these components instead of custom styling
- Don't override component styles unless absolutely necessary
- Keep variant usage consistent across pages

### 2. Accessibility
- All components have proper focus states
- Use aria-labels for icon-only buttons
- Ensure color contrast meets WCAG AA standards
- Use semantic HTML (button, label, input)

### 3. Loading States
- Show skeleton screens for data loading
- Use `loading` prop on buttons for async actions
- Disable buttons during loading

### 4. Error Handling
- Use Alert component for errors
- Show form validation errors inline
- Provide helpful error messages

### 5. Responsive Design
- Components are responsive by default
- Use Tailwind breakpoints (sm, md, lg, xl)
- Test on mobile, tablet, and desktop

---

## Component Status

✓ Button — Ready to use
✓ Card — Ready to use
✓ Alert — Ready to use
✓ Form — Ready to use
✓ Table — Ready to use
✓ Badge — Ready to use
✓ Skeleton — Ready to use
✓ EmptyState — Ready to use
✓ Modal — Ready to use
✓ Breadcrumb — Ready to use

---

## Migration Checklist

When updating existing pages:
- [ ] Replace custom button styles with Button component
- [ ] Replace card divs with CardComponent
- [ ] Replace alert divs with Alert component
- [ ] Replace form inputs with Form components
- [ ] Replace status badges with Badge component
- [ ] Add accessibility focus states
- [ ] Test on mobile and desktop
- [ ] Test keyboard navigation
- [ ] Verify color contrast

