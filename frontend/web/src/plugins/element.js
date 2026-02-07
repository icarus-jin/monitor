import Vue from 'vue'
import {
  Button, Form, FormItem, Input, Link, Row, Col, Message, Container, Header, Aside, Main,
  Menu, Submenu, MenuItem, RadioGroup, RadioButton, Divider, Breadcrumb, BreadcrumbItem,
  Table, TableColumn, Pagination, Dialog, MessageBox, Tag, Select, Option, Tree, Card,
  Cascader, Tabs, TabPane, Steps, Step, CheckboxGroup, Checkbox, Upload, Timeline, TimelineItem
} from 'element-ui'
import TreeTable from 'vue-table-with-tree-grid'
import VueQuillEditor from 'vue-quill-editor'

import 'quill/dist/quill.core.css'
import 'quill/dist/quill.snow.css'
import 'quill/dist/quill.bubble.css'

const elements = [
  Button, Form, FormItem, Input, Link, Row, Col, Container, Header, Aside, Main,
  Menu, Submenu, MenuItem, RadioGroup, RadioButton, Divider, Breadcrumb, BreadcrumbItem,
  Table, TableColumn, Pagination, Dialog, Tag, Select, Option, Tree, Card,
  Cascader, Tabs, TabPane, Steps, Step, CheckboxGroup, Checkbox, Upload, Timeline, TimelineItem
]

elements.forEach(el => Vue.use(el))

Vue.component('tree-table', TreeTable)
Vue.use(VueQuillEditor)

Vue.prototype.$message = Message
Vue.prototype.$confirm = MessageBox.confirm
Vue.prototype.$alert = MessageBox.alert
